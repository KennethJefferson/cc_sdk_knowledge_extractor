import { Command } from "commander";
import { resolve, isAbsolute } from "node:path";
import { existsSync, statSync, readdirSync } from "node:fs";
import type { CLIArguments, ValidatedCLIArguments } from "../types/index.ts";
import { GENERATOR_SKILLS, ERROR_CODES } from "../core/constants.ts";

export function parseArgs(): CLIArguments {
  const program = new Command();

  program
    .name("ccke")
    .description("CCKnowledgeExtractor - Extract course content and generate quizzes/exams")
    .version("0.1.0")
    .option("-i, --input <dir>", "Root directory containing courses")
    .option("-ccg, --ClaudeCodeGenerated <type>", "Content type to generate (e.g., 'Exam')")
    .option("-sw, --scanningworkers <n>", "Number of scanning workers", "1")
    .option("-w, --workers <n>", "Number of processing workers", "1")
    .option("-o, --output <dir>", "Output directory override")
    .option("-v, --verbose", "Enable verbose output", false)
    .option("--dry-run", "Preview processing without making changes", false)
    .option("--init-config", "Generate a sample .cckrc.json config file", false);

  program.parse();

  const opts = program.opts();

  return {
    input: (opts.input as string) ?? "",
    claudeCodeGenerated: (opts.ClaudeCodeGenerated as string) ?? "",
    scanningWorkers: parseInt(opts.scanningworkers as string, 10),
    workers: parseInt(opts.workers as string, 10),
    output: opts.output as string | undefined,
    verbose: opts.verbose as boolean,
    dryRun: opts.dryRun as boolean,
    initConfig: opts.initConfig as boolean,
  };
}

export interface ValidationResult {
  success: boolean;
  args?: ValidatedCLIArguments;
  error?: { code: string; message: string };
  warnings: string[];
}

export function validateArgs(args: CLIArguments): ValidationResult {
  const warnings: string[] = [];

  // Skip validation if --init-config is set (handled separately)
  if (args.initConfig) {
    return {
      success: true,
      args: {
        ...args,
        resolvedInput: args.input ? resolve(process.cwd(), args.input) : process.cwd(),
        targetSkill: "",
      },
      warnings,
    };
  }

  // Check required arguments
  if (!args.input) {
    return {
      success: false,
      error: {
        code: ERROR_CODES.INVALID_INPUT_PATH,
        message: "Missing required argument: -i, --input <dir>",
      },
      warnings,
    };
  }

  if (!args.claudeCodeGenerated) {
    return {
      success: false,
      error: {
        code: ERROR_CODES.SKILL_NOT_FOUND,
        message: "Missing required argument: -ccg, --ClaudeCodeGenerated <type>",
      },
      warnings,
    };
  }

  // Resolve input path
  const resolvedInput = isAbsolute(args.input) ? args.input : resolve(process.cwd(), args.input);

  // Check input exists
  if (!existsSync(resolvedInput)) {
    return {
      success: false,
      error: {
        code: ERROR_CODES.INVALID_INPUT_PATH,
        message: `Input directory does not exist: ${resolvedInput}`,
      },
      warnings,
    };
  }

  // Check input is a directory
  const inputStat = statSync(resolvedInput);
  if (!inputStat.isDirectory()) {
    return {
      success: false,
      error: {
        code: ERROR_CODES.INVALID_INPUT_PATH,
        message: `Input path is not a directory: ${resolvedInput}`,
      },
      warnings,
    };
  }

  // Check if user is inside a course folder (has .srt files in root)
  const rootFiles = readdirSync(resolvedInput);
  const hasSrtInRoot = rootFiles.some((f) => f.toLowerCase().endsWith(".srt"));
  if (hasSrtInRoot) {
    warnings.push(
      `WARNING: Found .srt files in input root. You may be inside a course folder. ` +
        `For multi-mode processing, run from the parent directory containing course folders.`
    );
  }

  // Validate -ccg argument (must have corresponding skill)
  const ccgNormalized = args.claudeCodeGenerated.toLowerCase().trim();
  const targetSkill = GENERATOR_SKILLS[ccgNormalized];

  if (!targetSkill) {
    const validTypes = Object.keys(GENERATOR_SKILLS).join(", ");
    return {
      success: false,
      error: {
        code: ERROR_CODES.SKILL_NOT_FOUND,
        message: `No generator skill found for content type '${args.claudeCodeGenerated}'. Valid types: ${validTypes}`,
      },
      warnings,
    };
  }

  // Resolve output path if provided
  let resolvedOutput: string | undefined;
  if (args.output) {
    resolvedOutput = isAbsolute(args.output) ? args.output : resolve(process.cwd(), args.output);
  }

  // Validate worker counts
  if (args.scanningWorkers < 1 || args.scanningWorkers > 16) {
    warnings.push(`Scanning workers clamped to valid range (1-16): was ${args.scanningWorkers}`);
  }
  if (args.workers < 1 || args.workers > 16) {
    warnings.push(`Processing workers clamped to valid range (1-16): was ${args.workers}`);
  }

  return {
    success: true,
    args: {
      ...args,
      scanningWorkers: Math.max(1, Math.min(16, args.scanningWorkers)),
      workers: Math.max(1, Math.min(16, args.workers)),
      resolvedInput,
      resolvedOutput,
      targetSkill,
    },
    warnings,
  };
}
