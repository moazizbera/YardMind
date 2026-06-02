import { spawn } from 'node:child_process'
import { mkdir } from 'node:fs/promises'
import net from 'node:net'
import path from 'node:path'
import process from 'node:process'
import { setTimeout as delay } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'

import { chromium } from 'playwright'

const __filename = fileURLToPath(import.meta.url)
const scriptsRoot = path.dirname(__filename)
const webRoot = path.resolve(scriptsRoot, '..')
const repoRoot = path.resolve(webRoot, '..')

function parseArgs(argv) {
  const options = {
    host: '127.0.0.1',
    port: 5173,
    outputDir: path.resolve(repoRoot, 'artifacts', 'demo'),
  }

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index]
    const nextValue = argv[index + 1]

    if (argument === '--host' && nextValue) {
      options.host = nextValue
      index += 1
    } else if (argument === '--port' && nextValue) {
      options.port = Number.parseInt(nextValue, 10)
      index += 1
    } else if (argument === '--output-dir' && nextValue) {
      options.outputDir = path.resolve(nextValue)
      index += 1
    }
  }

  return options
}

function checkPort(host, port) {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.unref()
    server.once('error', () => resolve(false))
    server.listen({ host, port }, () => {
      server.close(() => resolve(true))
    })
  })
}

async function findAvailablePort(host, startingPort) {
  let candidatePort = startingPort
  while (!(await checkPort(host, candidatePort))) {
    candidatePort += 1
  }
  return candidatePort
}

async function waitForServer(baseUrl, childProcess) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (childProcess.exitCode !== null) {
      throw new Error(`Vite exited early with code ${childProcess.exitCode}`)
    }

    try {
      const response = await fetch(baseUrl, { cache: 'no-store' })
      if (response.ok) {
        return
      }
    } catch {
      // Keep polling until Vite is ready or exits.
    }

    await delay(500)
  }

  throw new Error(`Timed out waiting for Vite at ${baseUrl}`)
}

async function captureView(browser, baseUrl, outputDir, view) {
  const page = await browser.newPage({ viewport: view.viewport })
  await page.goto(`${baseUrl}${view.route}`, { waitUntil: 'domcontentloaded' })

  for (const selector of view.waitForSelectors) {
    await page.locator(selector).waitFor({ state: 'visible' })
  }

  if (view.delayMs > 0) {
    await page.waitForTimeout(view.delayMs)
  }

  const filePath = path.join(outputDir, view.fileName)
  await page.screenshot({ fullPage: true, path: filePath, timeout: 60000 })
  await page.close()
  return filePath
}

async function main() {
  const options = parseArgs(process.argv.slice(2))
  const resolvedPort = await findAvailablePort(options.host, options.port)
  const baseUrl = `http://${options.host}:${resolvedPort}`
  const viteBinary =
    process.platform === 'win32'
      ? path.join(webRoot, 'node_modules', '.bin', 'vite.cmd')
      : path.join(webRoot, 'node_modules', '.bin', 'vite')
  const viteCommand = viteBinary
  const viteArgs = ['--host', options.host, '--port', `${resolvedPort}`, '--strictPort']

  await mkdir(options.outputDir, { recursive: true })
  console.log(`Starting capture server at ${baseUrl}`)

  const viteProcess = spawn(viteCommand, viteArgs, {
    cwd: webRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: process.platform === 'win32',
  })

  let browser
  try {
    viteProcess.stdout.on('data', (chunk) => process.stdout.write(chunk))
    viteProcess.stderr.on('data', (chunk) => process.stderr.write(chunk))

    await waitForServer(baseUrl, viteProcess)

    browser = await chromium.launch({ headless: true })

    const views = [
      {
        fileName: 'hackathon-frontend.png',
        route: '/?splash=0',
        viewport: { width: 1600, height: 1200 },
        waitForSelectors: ['h1:has-text("Lead with the yard state, keep the proof one click away.")', 'button:has-text("Open demo controls")'],
        delayMs: 500,
      },
      {
        fileName: 'hackathon-frontend-judge.png',
        route: '/?kiosk=1&autoplay=1',
        viewport: { width: 1600, height: 1200 },
        waitForSelectors: ['h2:has-text("Judge sequence")'],
        delayMs: 500,
      },
      {
        fileName: 'hackathon-frontend-organization.png',
        route: '/?view=organization',
        viewport: { width: 1600, height: 1200 },
        waitForSelectors: ['h2:has-text("Space organization view")', 'svg[aria-label="Ship arrival to organized yard flow"]', 'button[role="tab"]:has-text("Ship Flow")'],
        delayMs: 500,
      },
      {
        fileName: 'hackathon-frontend-equations.png',
        route: '/?view=equations',
        viewport: { width: 1600, height: 1200 },
        waitForSelectors: ['h2:has-text("Full equations")', 'text=Weighted objective'],
        delayMs: 500,
      },
      {
        fileName: 'hackathon-frontend-proof.png',
        route: '/?view=proof',
        viewport: { width: 1600, height: 1200 },
        waitForSelectors: ['h2:has-text("Submission proof view")', 'text=Lead with pass/fail, objective, and runtime'],
        delayMs: 500,
      },
      {
        fileName: 'hackathon-frontend-replay.png',
        route: '/?view=replay-stage&autoplay=1',
        viewport: { width: 1600, height: 1200 },
        waitForSelectors: ['h2:has-text("Fullscreen replay stage")', '.replay-scene-card h3:has-text("Official search replay")', '.replay-scene-stage-shell .showcase-stage-marker-pill:has-text("Live replay")'],
        delayMs: 800,
      },
    ]

    const writtenFiles = []
    for (const view of views) {
      const filePath = await captureView(browser, baseUrl, options.outputDir, view)
      writtenFiles.push(path.relative(repoRoot, filePath))
    }

    console.log('Captured demo screenshots:')
    for (const filePath of writtenFiles) {
      console.log(`- ${filePath}`)
    }
  } finally {
    if (browser) {
      await browser.close()
    }

    if (viteProcess.exitCode === null) {
      viteProcess.kill('SIGTERM')
      await Promise.race([
        new Promise((resolve) => viteProcess.once('exit', resolve)),
        delay(3000),
      ])
      if (viteProcess.exitCode === null) {
        viteProcess.kill('SIGKILL')
      }
    }
  }
}

main()
  .then(() => {
    process.exit(0)
  })
  .catch((error) => {
    console.error(error instanceof Error ? error.message : error)
    process.exit(1)
  })