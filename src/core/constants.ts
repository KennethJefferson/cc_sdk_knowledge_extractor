import type { FileCategory } from "../types/index.ts";

// File extensions by category
export const FILE_EXTENSIONS: Record<FileCategory, string[]> = {
  text: [".txt", ".md", ".csv", ".json", ".xml", ".srt", ".vtt", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"],
  code: [
    ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".lua",
    ".sh", ".bash", ".ps1", ".bat", ".cmd", ".sql", ".r", ".m", ".f90",
    ".asm", ".s", ".pl", ".pm", ".tcl", ".vim", ".el", ".clj", ".ex", ".exs",
    ".erl", ".hs", ".ml", ".fs", ".v", ".sv", ".vhd", ".vhdl"
  ],
  document: [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".odt", ".ods", ".odp"],
  database: [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".dbf", ".h2"],
  archive: [".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".tar.gz", ".tar.bz2", ".tar.xz"],
  image: [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg"],
  html: [".html", ".htm", ".xhtml", ".mhtml"],
  video: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg", ".3gp"],
  audio: [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".aiff"],
  unknown: [],
};

// Extensions to skip entirely (video/audio)
export const SKIP_EXTENSIONS = new Set([
  ...FILE_EXTENSIONS.video,
  ...FILE_EXTENSIONS.audio,
]);

// Extensions that are already text-readable (passthrough)
export const TEXT_EXTENSIONS = new Set([
  ...FILE_EXTENSIONS.text,
  ...FILE_EXTENSIONS.code,
]);

// Skill mapping by extension
export const SKILL_MAPPINGS: Record<string, { skill: string; outputFormat: string }> = {
  // Documents
  ".pdf": { skill: "pdf", outputFormat: ".md" },
  ".docx": { skill: "docx", outputFormat: ".md" },
  ".doc": { skill: "docx", outputFormat: ".md" },
  ".pptx": { skill: "pptx", outputFormat: ".md" },
  ".ppt": { skill: "pptx", outputFormat: ".md" },
  ".xlsx": { skill: "xlsx-processor", outputFormat: ".csv" },
  ".xls": { skill: "xlsx-processor", outputFormat: ".csv" },

  // Databases (route through db-identify first)
  ".db": { skill: "db-identify", outputFormat: ".csv" },
  ".sqlite": { skill: "db-identify", outputFormat: ".csv" },
  ".sqlite3": { skill: "db-identify", outputFormat: ".csv" },
  ".mdb": { skill: "db-identify", outputFormat: ".csv" },
  ".accdb": { skill: "db-identify", outputFormat: ".csv" },

  // HTML
  ".html": { skill: "html2markdown", outputFormat: ".md" },
  ".htm": { skill: "html2markdown", outputFormat: ".md" },

  // Images (OCR)
  ".png": { skill: "image-ocr", outputFormat: ".txt" },
  ".jpg": { skill: "image-ocr", outputFormat: ".txt" },
  ".jpeg": { skill: "image-ocr", outputFormat: ".txt" },
  ".gif": { skill: "image-ocr", outputFormat: ".txt" },
  ".bmp": { skill: "image-ocr", outputFormat: ".txt" },
  ".tiff": { skill: "image-ocr", outputFormat: ".txt" },
  ".tif": { skill: "image-ocr", outputFormat: ".txt" },

  // Archives
  ".zip": { skill: "archive-extractor", outputFormat: "directory" },
  ".rar": { skill: "archive-extractor", outputFormat: "directory" },
  ".7z": { skill: "archive-extractor", outputFormat: "directory" },
  ".tar": { skill: "archive-extractor", outputFormat: "directory" },
  ".gz": { skill: "archive-extractor", outputFormat: "directory" },
  ".tgz": { skill: "archive-extractor", outputFormat: "directory" },
  ".tar.gz": { skill: "archive-extractor", outputFormat: "directory" },
  ".tar.bz2": { skill: "archive-extractor", outputFormat: "directory" },
};

// Content generator skills (for -ccg argument)
export const GENERATOR_SKILLS: Record<string, string> = {
  exam: "quiz-generator",
  quiz: "quiz-generator",
  summary: "summary-generator",
  docs: "summary-generator",
  documentation: "summary-generator",
  // Future generators can be added here
  // sop: "sop-generator",
  // podcast: "podcast-generator",
  // tutorial: "tutorial-generator",
};

// Output directory names
export const OUTPUT_DIRS = {
  validatedFiles: "__cc_validated_files",
  codeFolder: "CODE",
  generatedPrefix: "__ccg_",
} as const;

// Error codes
export const ERROR_CODES = {
  // Validation errors
  SKILL_NOT_FOUND: "E001",
  INVALID_INPUT_PATH: "E002",
  NO_COURSES_FOUND: "E003",
  INSIDE_COURSE_FOLDER: "E004",

  // Processing errors
  FILE_READ_ERROR: "E101",
  FILE_WRITE_ERROR: "E102",
  SKILL_INVOCATION_FAILED: "E103",
  SKILL_TIMEOUT: "E104",

  // Routing errors
  UNSUPPORTED_FILE_TYPE: "E201",
  DB_ROUTING_FAILED: "E202",

  // System errors
  WORKER_CRASH: "E301",
  OUT_OF_MEMORY: "E302",
} as const;
