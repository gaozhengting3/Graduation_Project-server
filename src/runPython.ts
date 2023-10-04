import { spawn } from 'child_process'
import path from 'path'

const pythonScriptPath = path.join(process.cwd(), 'src', 'scripts', 'test.py')

const pythonProcess = spawn('python', [pythonScriptPath])

pythonProcess.stdout.on('data', (data) => {
  console.log(`Python script output: ${data}`)
})

pythonProcess.stderr.on('data', (data) => {
  console.error(`Python script error: ${data}`)
})

pythonProcess.on('close', (code) => {
  if (code === 0) {
    console.log('Python script executed successfully.')
  } else {
    console.error(`Python script exited with code ${code}`)
  }
})
