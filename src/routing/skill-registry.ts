import type { SkillInfo, RoutingDecision, RoutingMethod } from "../types/index.ts";
import {
  TEXT_EXTENSIONS,
  SKIP_EXTENSIONS,
  SKILL_MAPPINGS,
  GENERATOR_SKILLS,
} from "../core/constants.ts";

export class SkillRegistry {
  private skills: Map<string, SkillInfo> = new Map();

  constructor() {
    this.registerDefaultSkills();
  }

  private registerDefaultSkills(): void {
    // Document processors
    this.register({
      name: "pdf",
      description: "Extract text and tables from PDF files",
      supportedExtensions: [".pdf"],
      outputFormat: ".md",
      isGenerator: false,
    });

    this.register({
      name: "docx",
      description: "Extract content from Word documents",
      supportedExtensions: [".docx", ".doc"],
      outputFormat: ".md",
      isGenerator: false,
    });

    this.register({
      name: "pptx",
      description: "Extract content from PowerPoint presentations",
      supportedExtensions: [".pptx", ".ppt"],
      outputFormat: ".md",
      isGenerator: false,
    });

    this.register({
      name: "xlsx-processor",
      description: "Extract data from spreadsheets",
      supportedExtensions: [".xlsx", ".xls", ".xlsm"],
      outputFormat: ".csv",
      isGenerator: false,
    });

    // Database processors
    this.register({
      name: "db-extractor-sqlite",
      description: "Extract SQLite database to CSV/JSON/Markdown",
      supportedExtensions: [".db", ".sqlite", ".sqlite3"],
      outputFormat: ".csv",
      isGenerator: false,
    });

    this.register({
      name: "db-identify",
      description: "Identify database format",
      supportedExtensions: [".mdb", ".accdb"],
      outputFormat: ".json",
      isGenerator: false,
    });

    // Converters
    this.register({
      name: "html2markdown",
      description: "Convert HTML to Markdown",
      supportedExtensions: [".html", ".htm", ".xhtml"],
      outputFormat: ".md",
      isGenerator: false,
    });

    // Image OCR
    this.register({
      name: "image-ocr",
      description: "Extract text from images using OCR",
      supportedExtensions: [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"],
      outputFormat: ".txt",
      isGenerator: false,
    });

    // Archive extractor
    this.register({
      name: "archive-extractor",
      description: "Extract archives using 7-Zip",
      supportedExtensions: [".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".tar.gz", ".tar.bz2"],
      outputFormat: "directory",
      isGenerator: false,
    });

    // Content generators
    this.register({
      name: "quiz-generator",
      description: "Generate quiz/exam content from course materials",
      supportedExtensions: [],
      outputFormat: ".md",
      isGenerator: true,
    });

    this.register({
      name: "summary-generator",
      description: "Generate documentation and summaries from course materials",
      supportedExtensions: [],
      outputFormat: ".md",
      isGenerator: true,
    });
  }

  register(skill: SkillInfo): void {
    this.skills.set(skill.name, skill);
  }

  get(name: string): SkillInfo | undefined {
    return this.skills.get(name);
  }

  has(name: string): boolean {
    return this.skills.has(name);
  }

  getByExtension(extension: string): SkillInfo | undefined {
    const ext = extension.toLowerCase();
    for (const skill of this.skills.values()) {
      if (skill.supportedExtensions.includes(ext)) {
        return skill;
      }
    }
    return undefined;
  }

  getGenerators(): SkillInfo[] {
    return Array.from(this.skills.values()).filter((s) => s.isGenerator);
  }

  getProcessors(): SkillInfo[] {
    return Array.from(this.skills.values()).filter((s) => !s.isGenerator);
  }

  /**
   * Determine routing decision for a file based on its extension.
   */
  getRoutingDecision(extension: string): RoutingDecision {
    const ext = extension.toLowerCase();

    // Check if video/audio (skip)
    if (SKIP_EXTENSIONS.has(ext)) {
      return {
        method: "skip" as RoutingMethod,
        metadata: { reason: "Video/audio files are skipped" },
      };
    }

    // Check if text-based (passthrough)
    if (TEXT_EXTENSIONS.has(ext)) {
      return {
        method: "passthrough" as RoutingMethod,
        outputFormat: ext,
      };
    }

    // Check skill mapping
    const mapping = SKILL_MAPPINGS[ext];
    if (mapping) {
      // Special handling for archives
      if (mapping.outputFormat === "directory") {
        return {
          method: "archive" as RoutingMethod,
          skillName: mapping.skill,
          outputFormat: mapping.outputFormat,
        };
      }

      return {
        method: "skill" as RoutingMethod,
        skillName: mapping.skill,
        outputFormat: mapping.outputFormat,
      };
    }

    // Unknown file type
    return {
      method: "unsupported" as RoutingMethod,
      metadata: { extension: ext },
    };
  }

  /**
   * Get generator skill name for content type.
   */
  getGeneratorSkill(contentType: string): string | undefined {
    const normalized = contentType.toLowerCase().trim();
    return GENERATOR_SKILLS[normalized];
  }

  /**
   * List all registered skills.
   */
  list(): SkillInfo[] {
    return Array.from(this.skills.values());
  }
}

// Singleton instance
export const skillRegistry = new SkillRegistry();
