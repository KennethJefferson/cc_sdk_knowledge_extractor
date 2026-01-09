// CLI Types
export interface CLIArguments {
  input: string;
  scanningWorkers: number;
  workers: number;
  output?: string;
  claudeCodeGenerated: string;
  verbose: boolean;
  dryRun: boolean;
  initConfig: boolean;
}

export interface ValidatedCLIArguments extends CLIArguments {
  resolvedInput: string;
  resolvedOutput?: string;
  targetSkill: string;
}

// File Types
export type FileCategory =
  | "text"
  | "code"
  | "document"
  | "database"
  | "archive"
  | "image"
  | "html"
  | "video"
  | "audio"
  | "unknown";

export interface ScannedFile {
  path: string;
  relativePath: string;
  name: string;
  extension: string;
  size: number;
  category: FileCategory;
  courseId: string;
  coursePath: string;
}

export interface Course {
  id: string;
  name: string;
  path: string;
  codePath: string;
  validatedFilesPath: string;
  generatedPath: string;
  files: ScannedFile[];
  hasExistingSrt: boolean;
}

// Queue Types
export type QueueItemStatus =
  | "pending"
  | "scanning"
  | "routing"
  | "processing"
  | "completed"
  | "failed"
  | "skipped";

export type ProcessingStage = "scan" | "route" | "convert" | "validate" | "generate";

export interface QueueItem {
  id: string;
  file: ScannedFile;
  status: QueueItemStatus;
  stage: ProcessingStage;
  priority: number;
  attempts: number;
  maxAttempts: number;
  routedTo?: RoutingDecision;
  outputPath?: string;
  error?: ProcessingError;
  startedAt?: Date;
  completedAt?: Date;
}

export interface QueueStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  skipped: number;
}

// Routing Types
export type RoutingMethod =
  | "passthrough"
  | "skill"
  | "archive"
  | "skip"
  | "unsupported";

export interface RoutingDecision {
  method: RoutingMethod;
  skillName?: string;
  skillPrompt?: string;
  outputFormat?: string;
  requiresSubrouting?: boolean;
  metadata?: Record<string, unknown>;
}

export interface SkillInfo {
  name: string;
  description: string;
  supportedExtensions: string[];
  outputFormat: string;
  isGenerator: boolean;
}

// Result Types
export interface ProcessingResult {
  queueItem: QueueItem;
  success: boolean;
  outputPath?: string;
  outputSize?: number;
  duration: number;
  tokensUsed?: number;
  costUsd?: number;
  warnings: string[];
}

export interface ProcessingError {
  code: string;
  message: string;
  stack?: string;
  recoverable: boolean;
  context?: Record<string, unknown>;
}

export interface CourseProcessingResult {
  course: Course;
  stats: QueueStats;
  results: ProcessingResult[];
  errors: ProcessingError[];
  totalDuration: number;
  totalTokens: number;
  totalCost: number;
}

export interface AppResult {
  success: boolean;
  courses: CourseProcessingResult[];
  totalStats: QueueStats;
  errorLogPath?: string;
  startTime: Date;
  endTime: Date;
}

// Skill Invocation Types
export interface SkillInvocationConfig {
  skillName: string;
  prompt: string;
  filePath: string;
  outputPath: string;
  workingDirectory: string;
  timeout?: number;
}

export interface SkillInvocationResult {
  success: boolean;
  outputPath?: string;
  messages: unknown[];
  result?: unknown;
  duration: number;
  error?: ProcessingError;
}

// Logging Types
export interface LogEntry {
  timestamp: Date;
  level: "info" | "warn" | "error";
  code?: string;
  message: string;
  file?: string;
  context?: Record<string, unknown>;
}
