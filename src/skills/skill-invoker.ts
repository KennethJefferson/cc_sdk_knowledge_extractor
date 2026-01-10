import { spawn } from "node:child_process";
import { resolve } from "node:path";
import type {
  SkillInvocationConfig,
  SkillInvocationResult,
  ProcessingError,
} from "../types/index.ts";

// Note: The Claude Agent SDK is used for complex AI-driven tasks.
// For simple skill invocations (Python scripts), we use direct subprocess calls
// to avoid SDK overhead and token costs.

export class SkillInvoker {
  private readonly skillsDir: string;

  constructor(projectRoot: string) {
    this.skillsDir = resolve(projectRoot, "skills");
  }

  /**
   * Invoke a skill by running its Python script directly.
   * This is used for deterministic file processing skills.
   */
  async invokeScript(config: SkillInvocationConfig): Promise<SkillInvocationResult> {
    const startTime = Date.now();
    const scriptPath = resolve(
      this.skillsDir,
      config.skillName,
      "scripts",
      this.getScriptName(config.skillName)
    );

    const args = this.buildArgs(config);

    try {
      const result = await this.runPythonScript(scriptPath, args, config.timeout);

      return {
        success: result.success,
        outputPath: config.outputPath,
        messages: [],
        result: result.output,
        duration: Date.now() - startTime,
        error: result.error,
      };
    } catch (error) {
      return {
        success: false,
        messages: [],
        duration: Date.now() - startTime,
        error: this.mapError(error),
      };
    }
  }

  private getScriptName(skillName: string): string {
    const scriptMap: Record<string, string> = {
      "file-router": "file_router.py",
      "image-ocr": "image_ocr.py",
      "archive-extractor": "archive_extract.py",
      "quiz-generator": "quiz_generate.py",
      "summary-generator": "summary_generate.py",
      "sop-generator": "sop_generate.py",
      "project-maker": "project_maker.py",
      "db-identify": "db_identify.py",
      "db-router": "db_route.py",
      "db-extractor-sqlite": "db_extract.py",
      "db-extractor-mysql": "db_extract.py",
      html2markdown: "html2markdown.py",
      pdf: "extract_text.py",
      docx: "extract_text.py",
      pptx: "extract_text.py",
      "xlsx-processor": "extract_data.py",
    };
    return scriptMap[skillName] ?? `${skillName.replace(/-/g, "_")}.py`;
  }

  private buildArgs(config: SkillInvocationConfig): string[] {
    const args: string[] = [];

    // Add input file
    if (config.filePath) {
      args.push(config.filePath);
    }

    // Add output option if specified
    if (config.outputPath) {
      args.push("-o", config.outputPath);
    }

    // Always request JSON output for parsing
    args.push("--json");

    return args;
  }

  private async runPythonScript(
    scriptPath: string,
    args: string[],
    timeout?: number
  ): Promise<{ success: boolean; output: unknown; error?: ProcessingError }> {
    return new Promise((resolve) => {
      const proc = spawn("python", [scriptPath, ...args], {
        stdio: ["pipe", "pipe", "pipe"],
        timeout: timeout ?? 120000, // 2 minutes default
      });

      let stdout = "";
      let stderr = "";

      proc.stdout?.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr?.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        if (code === 0) {
          try {
            const output = JSON.parse(stdout);
            if (output.error) {
              resolve({
                success: false,
                output,
                error: {
                  code: "SKILL_ERROR",
                  message: output.error,
                  recoverable: false,
                },
              });
            } else {
              resolve({ success: true, output });
            }
          } catch {
            // Not JSON, return raw output
            resolve({ success: true, output: stdout });
          }
        } else {
          resolve({
            success: false,
            output: null,
            error: {
              code: "SCRIPT_FAILED",
              message: stderr || `Script exited with code ${code}`,
              recoverable: false,
            },
          });
        }
      });

      proc.on("error", (error) => {
        resolve({
          success: false,
          output: null,
          error: {
            code: "SPAWN_ERROR",
            message: error.message,
            recoverable: false,
          },
        });
      });
    });
  }

  private mapError(error: unknown): ProcessingError {
    if (error instanceof Error) {
      return {
        code: "INVOCATION_ERROR",
        message: error.message,
        stack: error.stack,
        recoverable: false,
      };
    }
    return {
      code: "UNKNOWN_ERROR",
      message: String(error),
      recoverable: false,
    };
  }

  /**
   * Route a file through the file-router skill to determine processor.
   */
  async routeFile(filePath: string): Promise<{
    fileType: string;
    processor: string | null;
    confidence: string;
    detectionMethod: string;
    error?: string;
  }> {
    const result = await this.invokeScript({
      skillName: "file-router",
      prompt: "",
      filePath,
      outputPath: "",
      workingDirectory: this.skillsDir,
    });

    if (!result.success || !result.result) {
      return {
        fileType: "unknown",
        processor: null,
        confidence: "none",
        detectionMethod: "none",
        error: result.error?.message ?? "Failed to route file",
      };
    }

    const output = result.result as Record<string, unknown>;
    return {
      fileType: (output.file_type as string) ?? "unknown",
      processor: (output.processor as string) ?? null,
      confidence: (output.confidence as string) ?? "none",
      detectionMethod: (output.detection_method as string) ?? "none",
      error: output.error as string | undefined,
    };
  }
}
