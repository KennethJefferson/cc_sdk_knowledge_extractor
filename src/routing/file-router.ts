import type { ScannedFile, RoutingDecision, QueueItem } from "../types/index.ts";
import { skillRegistry } from "./skill-registry.ts";
import { SkillInvoker } from "../skills/skill-invoker.ts";
import { TEXT_EXTENSIONS, SKIP_EXTENSIONS } from "../core/constants.ts";

export class FileRouter {
  private skillInvoker: SkillInvoker;
  private useSkillForRouting: boolean;

  constructor(projectRoot: string, useSkillForRouting: boolean = false) {
    this.skillInvoker = new SkillInvoker(projectRoot);
    this.useSkillForRouting = useSkillForRouting;
  }

  /**
   * Route a file to determine how it should be processed.
   * Uses local extension-based routing by default, or skill-based for accuracy.
   */
  async route(file: ScannedFile): Promise<RoutingDecision> {
    // Fast path: use extension-based routing from registry
    if (!this.useSkillForRouting) {
      return this.routeByExtension(file);
    }

    // Slower but more accurate: use file-router skill with magic bytes
    return this.routeBySkill(file);
  }

  /**
   * Route based on file extension (fast).
   */
  routeByExtension(file: ScannedFile): RoutingDecision {
    return skillRegistry.getRoutingDecision(file.extension);
  }

  /**
   * Route using the file-router skill (accurate, uses magic bytes).
   */
  async routeBySkill(file: ScannedFile): Promise<RoutingDecision> {
    const result = await this.skillInvoker.routeFile(file.path);

    if (result.error) {
      return {
        method: "unsupported",
        metadata: { error: result.error },
      };
    }

    // Map skill result to routing decision
    if (result.processor === "skip") {
      return { method: "skip" };
    }

    if (result.processor === "passthrough") {
      return {
        method: "passthrough",
        outputFormat: file.extension,
      };
    }

    if (result.processor === "archive-extractor") {
      return {
        method: "archive",
        skillName: result.processor,
        outputFormat: "directory",
      };
    }

    if (result.processor) {
      return {
        method: "skill",
        skillName: result.processor,
        metadata: {
          fileType: result.fileType,
          confidence: result.confidence,
          detectionMethod: result.detectionMethod,
        },
      };
    }

    return {
      method: "unsupported",
      metadata: { fileType: result.fileType },
    };
  }

  /**
   * Route multiple files.
   */
  async routeMany(files: ScannedFile[]): Promise<Map<string, RoutingDecision>> {
    const results = new Map<string, RoutingDecision>();

    for (const file of files) {
      const decision = await this.route(file);
      results.set(file.path, decision);
    }

    return results;
  }

  /**
   * Categorize files by routing method.
   */
  categorizeByMethod(
    files: ScannedFile[],
    decisions: Map<string, RoutingDecision>
  ): {
    passthrough: ScannedFile[];
    skill: ScannedFile[];
    archive: ScannedFile[];
    skip: ScannedFile[];
    unsupported: ScannedFile[];
  } {
    const result = {
      passthrough: [] as ScannedFile[],
      skill: [] as ScannedFile[],
      archive: [] as ScannedFile[],
      skip: [] as ScannedFile[],
      unsupported: [] as ScannedFile[],
    };

    for (const file of files) {
      const decision = decisions.get(file.path);
      if (!decision) continue;

      switch (decision.method) {
        case "passthrough":
          result.passthrough.push(file);
          break;
        case "skill":
          result.skill.push(file);
          break;
        case "archive":
          result.archive.push(file);
          break;
        case "skip":
          result.skip.push(file);
          break;
        case "unsupported":
          result.unsupported.push(file);
          break;
      }
    }

    return result;
  }

  /**
   * Get output path for a processed file.
   */
  getOutputPath(
    file: ScannedFile,
    decision: RoutingDecision,
    validatedFilesPath: string
  ): string {
    const { join, basename, dirname, relative } = require("node:path");

    // Flatten directory structure with prefix
    const relDir = relative(file.coursePath, dirname(file.path));
    const prefix = relDir ? relDir.replace(/[\\/]/g, "_") + "_" : "";

    // Determine output extension
    let outputExt = file.extension;
    if (decision.outputFormat && decision.outputFormat !== "directory") {
      outputExt = decision.outputFormat;
    }

    const baseName = basename(file.name, file.extension);
    const outputName = `${prefix}${baseName}${outputExt}`;

    return join(validatedFilesPath, outputName);
  }
}
