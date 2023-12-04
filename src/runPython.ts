import { spawn } from 'child_process'
import path from 'path'

const pythonScriptPath = path.join(process.cwd(), 'src', 'scripts', 'backend.py')

const startProcess = (): void => {
  const pythonProcess = spawn('python', [pythonScriptPath])

  pythonProcess.stdout.on('data', (data) => {
    console.log(`${data}`)
  })

  pythonProcess.stderr.on('data', (data) => {
    console.error(`${data}`)
  })

  pythonProcess.on('close', (code) => {
    if (code === 0) {
      console.error('===================================\nPython server deon.\n===================================')
    } else {
      console.error(`===================================\nPython server exited with code ${code}\n===================================`)
      startProcess()
    }
  })
}

startProcess()
