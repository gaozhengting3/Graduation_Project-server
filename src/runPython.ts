import { spawn } from 'child_process'
import path from 'path'

const pythonScriptPath = path.join(process.cwd(), 'src', 'scripts', 'backend.py')

const pythonProcess = spawn('python', [pythonScriptPath])

pythonProcess.stdout.on('data', (data) => {
  console.log(`Python server output: ${data}`)
})

pythonProcess.stderr.on('data', (data) => {
  console.error(`Python server error: ${data}`)
})

pythonProcess.on('close', (code) => {
  if (code === 0) {
    console.error('Python server died.')
  } else {
    console.error(`Python server exited with code ${code}`)
  }
})
