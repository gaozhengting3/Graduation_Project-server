import CourseModel from '@/models/CourseModel'
import Axios from 'axios'
import { type Request, type Response } from 'express'
import path from 'path'
import { v4 } from 'uuid'

// const waitForTimeout = async (seconds: number): Promise<void> => { await new Promise((resolve) => setTimeout(resolve, seconds)) }

const courseController = {
  insertOne: async (req: Request, res: Response) => {
    const { courseID, title, subtitle, description, instructor, image, goals, students } = req.body
    try {
      const course = await CourseModel.find({ courseID })
      // console.log(course)
      // return res.status(200).json({ success: true, message: 'New course has been created.' })
      if (course.length > 0) return res.status(403).json({ success: false, message: 'The course has already existed.' })
      const newCourse = new CourseModel({ courseID, title, subtitle, description, instructor, image, goals, students })
      await newCourse.save()
      return res.status(500).json({})
    } catch (error) {
      console.log(error)
      return res.status(500).send({ success: false, error })
    }
  },
  getOne: async (req: Request, res: Response) => {
    try {
      const course = await CourseModel.find({})
      return res.status(200).json({ success: true, data: course })
    } catch (error) {
      console.log(error)
      return res.status(500).send({ success: false, error })
    }
  },
  rollCallByImage: async (req: Request, res: Response) => {
    const file = req.files?.image

    if (file === undefined || Array.isArray(file)) {
      return res.status(400).send({ success: false, file: { url: 'No file was uploaded or too many files were uploaded.' } })
    }

    const sampleFile = file
    const fileName = v4() + '-' + sampleFile?.name
    const rootPath = path.dirname(path.dirname(__dirname))
    const dirPath = path.join(rootPath, 'private', 'roll_call_original')
    const uploadPath = path.join(dirPath, fileName)
    // const fileURL = `${process.env.HOST ?? 'http://localhost'}:${process.env.PORT ?? '8000'}/uploads/${fileName}`
    console.log(uploadPath)
    sampleFile.mv(uploadPath, async (err) => {
      if (err !== undefined) return res.status(500).send({ success: false, message: 'Something went wrong.' })
      else {
        try {
          const URL = `${process.env.PYTHON_HOST_Local ?? 'http://localhost:8001'}`
          console.log('POST to : ', URL)
          const response = await Axios.post(URL, { fileName })
          console.log(response.data)
          return res.send({ success: true })
        } catch (error) {
          return res.status(500).send({ success: false, message: 'Something went wrong.' })
        }
      }
    })
  }
}
export default courseController
