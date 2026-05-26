import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = resolve(fileURLToPath(new URL("..", import.meta.url)));
const isWindows = process.platform === "win32";
const apiHost = process.env.API_HOST || "127.0.0.1";
const apiPort = process.env.API_PORT || "8000";
const webHost = process.env.WEB_HOST || "127.0.0.1";
const webPort = process.env.WEB_PORT || "3000";

loadDotEnv(join(rootDir, ".env.local"));

process.env.API_CORS_ORIGINS =
  process.env.API_CORS_ORIGINS ||
  `http://localhost:${webPort},http://127.0.0.1:${webPort},http://localhost:3001,http://127.0.0.1:3001`;

const python = findPython();
const nextBin = join(rootDir, "node_modules", "next", "dist", "bin", "next");
const children = [];

console.log(`Starting FastAPI on http://${apiHost}:${apiPort}`);
children.push(
  spawn(
    python,
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--app-dir",
      "apps/api",
      "--reload",
      "--host",
      apiHost,
      "--port",
      apiPort,
    ],
    childOptions()
  )
);

console.log(`Starting Next.js on http://${webHost}:${webPort}`);
children.push(
  spawn(
    process.execPath,
    [nextBin, "dev", "--hostname", webHost, "--port", webPort],
    childOptions({ cwd: join(rootDir, "apps", "web") })
  )
);

console.log("");
console.log(`Frontend: http://${webHost}:${webPort}`);
console.log(`Backend:  http://${apiHost}:${apiPort}`);
console.log("Press Ctrl-C to stop both servers.");
console.log("");

for (const child of children) {
  child.on("exit", (code, signal) => {
    if (signal) {
      shutdown(signal);
      return;
    }
    if (code && code !== 0) {
      shutdown(`child exited with code ${code}`, code);
    }
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

function childOptions(overrides = {}) {
  return {
    cwd: rootDir,
    env: process.env,
    shell: false,
    stdio: "inherit",
    windowsHide: false,
    ...overrides,
  };
}

function shutdown(reason, exitCode = 0) {
  for (const child of children) {
    if (!child.killed) {
      child.kill();
    }
  }
  process.exit(exitCode);
}

function findPython() {
  const localCandidates = isWindows
    ? [
        join(rootDir, ".venv", "Scripts", "python.exe"),
        join(process.env.LOCALAPPDATA || "", "Programs", "Python", "Python312", "python.exe"),
        join(process.env.LOCALAPPDATA || "", "Programs", "Python", "Python311", "python.exe"),
        join(process.env.LOCALAPPDATA || "", "Programs", "Python", "Python310", "python.exe"),
      ]
    : [join(rootDir, ".venv", "bin", "python"), "python3", "python"];

  for (const candidate of localCandidates) {
    if (candidate.includes("\\") || candidate.includes("/")) {
      if (existsSync(candidate)) {
        return candidate;
      }
    } else {
      return candidate;
    }
  }

  return isWindows ? "python" : "python3";
}


function loadDotEnv(filePath) {
  if (!existsSync(filePath)) {
    return;
  }

  for (const line of readFileSync(filePath, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const equalsIndex = trimmed.indexOf("=");
    if (equalsIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, equalsIndex).trim();
    const value = trimmed.slice(equalsIndex + 1).trim().replace(/^['"]|['"]$/g, "");
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}
