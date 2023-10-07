// import useRoutes from './routes'
import 'module-alias/register'

import 'dotenv/config'

import cors from 'cors'
import express from 'express'
import http from 'http'
import morgan from 'morgan'
import path from 'path'

import useRoutes from '@/routes'
import fileUpload from 'express-fileupload'
import mongoose from 'mongoose'

// import '@/runPython'

// merge test

mongoose
  .connect(process.env.mongoConnect ?? '', {
    // useNewUrlParser: true,
    // useUnifiedTopology: true
  })
  .then(() => { console.log('Connect to mongodb success.') })
  .catch((err: Error) => { console.log('err :>> ', err, 'Connect to mongodb failed!') })

const app = express()
const server = http.createServer(app)
const publicPath = path.join(path.dirname(__dirname), 'public', 'static')

// -- middleware --//
app.use(cors())
app.use(fileUpload())
app.use(express.json())
app.use(express.static(publicPath))
app.use(express.urlencoded({ extended: true }))
app.use(morgan('dev'))

// -- routes --//
useRoutes(app)

app.get('/*', (_, res) => res.status(404).send({ success: false, message: 'route not found' }))

server.listen(process.env.PORT ?? 8000, () => { console.log(`Server is running on http://localhost:${process.env.PORT ?? 8000}.`) })
