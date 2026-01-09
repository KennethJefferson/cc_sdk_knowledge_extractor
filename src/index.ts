#!/usr/bin/env bun
import { resolve, join } from "node:path";
import { writeFileSync, existsSync } from "node:fs";
import { parseArgs, validateArgs } from "./cli/args.ts";
import { App } from "./core/app.ts";
import { logger } from "./logging/logger.ts";
import { loadConfig, mergeWithConfig, generateSampleConfig } from "./core/config.ts";

async function main(): Promise<void> {
  console.log("CCKnowledgeExtractor v0.1.0\n");

  // Parse CLI arguments
  let args = parseArgs();

  // Handle --init-config early
  if (args.initConfig) {
    const targetDir = args.input ? resolve(process.cwd(), args.input) : process.cwd();
    const configPath = join(targetDir, ".cckrc.json");

    if (existsSync(configPath)) {
      console.log(`Config file already exists: ${configPath}`);
      console.log("Delete it first if you want to regenerate.");
      process.exit(1);
    }

    const content = generateSampleConfig();
    writeFileSync(configPath, content, "utf-8");
    console.log(`Created sample config file: ${configPath}`);
    console.log("\nEdit the file to customize your settings.");
    process.exit(0);
  }

  // Load config file from input directory
  const config = loadConfig(args.input);
  if (config) {
    logger.debug("Loaded config file");
    args = mergeWithConfig(args, config);
  }

  // Validate arguments
  const validation = validateArgs(args);

  // Print warnings
  for (const warning of validation.warnings) {
    logger.warn(warning);
  }

  // Exit on validation error
  if (!validation.success || !validation.args) {
    logger.error(`${validation.error?.code}: ${validation.error?.message}`);
    process.exit(1);
  }

  const validatedArgs = validation.args;

  // Set verbose mode
  logger.setVerbose(validatedArgs.verbose);

  console.log("Configuration:");
  console.log(`  Input:             ${validatedArgs.resolvedInput}`);
  console.log(`  Content Type:      ${validatedArgs.claudeCodeGenerated}`);
  console.log(`  Target Skill:      ${validatedArgs.targetSkill}`);
  console.log(`  Scanning Workers:  ${validatedArgs.scanningWorkers}`);
  console.log(`  Processing Workers: ${validatedArgs.workers}`);
  if (validatedArgs.resolvedOutput) {
    console.log(`  Output Override:   ${validatedArgs.resolvedOutput}`);
  }
  if (validatedArgs.verbose) {
    console.log(`  Verbose:           enabled`);
  }
  if (validatedArgs.dryRun) {
    console.log(`  Dry Run:           enabled (no changes will be made)`);
  }
  console.log("");

  // Get project root (where this script is located)
  const projectRoot = resolve(import.meta.dir, "..");

  // Create and run the application
  const app = new App(validatedArgs, projectRoot);

  try {
    const result = await app.run();

    if (result.success) {
      console.log("\nAll processing completed successfully!");
      process.exit(0);
    } else {
      console.log("\nProcessing completed with errors. Check error logs for details.");
      process.exit(1);
    }
  } catch (error) {
    logger.error(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
