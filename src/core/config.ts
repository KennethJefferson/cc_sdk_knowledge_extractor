import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import type { CLIArguments } from "../types/index.ts";

export interface ConfigFile {
  // Default values for CLI arguments
  defaults?: {
    scanningWorkers?: number;
    workers?: number;
    verbose?: boolean;
    contentType?: string;
  };

  // Exclude patterns for file scanning
  exclude?: string[];

  // Custom skill mappings
  skills?: Record<string, string>;

  // Output directory customization
  output?: {
    validatedDir?: string;
    generatedPrefix?: string;
  };
}

const CONFIG_FILE_NAMES = [".cckrc.json", ".cckrc", "ccke.config.json"];

/**
 * Find and load config file from the given directory or its parents.
 */
export function loadConfig(startDir: string): ConfigFile | null {
  let currentDir = resolve(startDir);
  const root = resolve("/");

  while (currentDir !== root) {
    for (const fileName of CONFIG_FILE_NAMES) {
      const configPath = join(currentDir, fileName);
      if (existsSync(configPath)) {
        try {
          const content = readFileSync(configPath, "utf-8");
          return JSON.parse(content) as ConfigFile;
        } catch (error) {
          console.warn(`Warning: Failed to parse config file ${configPath}`);
          return null;
        }
      }
    }
    currentDir = resolve(currentDir, "..");
  }

  return null;
}

/**
 * Merge config file defaults with CLI arguments.
 * CLI arguments take precedence over config file.
 */
export function mergeWithConfig(
  args: CLIArguments,
  config: ConfigFile | null
): CLIArguments {
  if (!config?.defaults) {
    return args;
  }

  const defaults = config.defaults;

  return {
    ...args,
    scanningWorkers: args.scanningWorkers || defaults.scanningWorkers || 1,
    workers: args.workers || defaults.workers || 1,
    verbose: args.verbose || defaults.verbose || false,
    // Don't override claudeCodeGenerated from config - it's required from CLI
  };
}

/**
 * Get exclude patterns from config.
 */
export function getExcludePatterns(config: ConfigFile | null): string[] {
  return config?.exclude ?? [];
}

/**
 * Get custom output directory names from config.
 */
export function getOutputConfig(config: ConfigFile | null): {
  validatedDir: string;
  generatedPrefix: string;
} {
  return {
    validatedDir: config?.output?.validatedDir ?? "__cc_validated_files",
    generatedPrefix: config?.output?.generatedPrefix ?? "__ccg_",
  };
}

/**
 * Generate a sample config file content.
 */
export function generateSampleConfig(): string {
  const sample: ConfigFile = {
    defaults: {
      scanningWorkers: 2,
      workers: 4,
      verbose: false,
      contentType: "Exam",
    },
    exclude: [
      "node_modules",
      ".git",
      "*.log",
    ],
    output: {
      validatedDir: "__cc_validated_files",
      generatedPrefix: "__ccg_",
    },
  };

  return JSON.stringify(sample, null, 2);
}
