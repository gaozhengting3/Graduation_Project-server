import Course, { type TCourse } from '@/models/Course'
import Axios from 'axios'
import { type Request, type Response } from 'express'
import { existsSync, mkdirSync } from 'fs'
import { readFile } from 'fs/promises'
import path from 'path'
import { v4 } from 'uuid'

import Attendant, { type TAttendance } from '@/models/Attendant'
import User from '@/models/User'
import type mongoose from 'mongoose'

let coursesData: any[]
const rootPath = path.dirname(path.dirname(__dirname))
void (async function readJsonFile () {
  try {
    const rawData = await readFile('./data/courses.json', 'utf8')
    const jsonData: any[] = JSON.parse(rawData)
    coursesData = jsonData.filter((course) => course['教師姓名'] === '李國川')
  } catch (error) {
    console.error('Error reading or parsing JSON file:', error)
  }
})()

const courseController = {
  insertCourse: async (req: Request, res: Response) => {
    const { courseID, title, subtitle, description, instructor, image, goals, students } = req.body
    try {
      const course = await Course.find({ courseID })
      // console.log(course)
      // return res.status(200).json({ success: true, message: 'New course has been created.' })
      if (course.length > 0) {
        return res
          .status(403)
          .json({ success: false, message: 'The course has already existed.' })
      }
      const newCourse = new Course({
        courseID,
        title,
        subtitle,
        description,
        instructor,
        image,
        goals,
        students
      })
      await newCourse.save()
      return res.status(500).json({})
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'The course has already existed.' })
    }
  },
  getCourseByID: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      const course = await Course.findOne({ courseID })
      return res.status(200).json({ success: true, data: { course } })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },

  getAllCourses: async (req: Request, res: Response) => {
    try {
      const courses = await Course.find({})
      return res.status(200).json({ success: true, data: courses })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  getCoursesByInstructor: async (req: Request, res: Response) => {
    try {
      const { instructor } = req.params
      const courses = await Course.find({ instructor })

      return res.status(200).json({ success: true, data: { courses } })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  updateCourseStudents: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      const { students } = req.body
      const course = await Course.findOne({ courseID })
      const result = await course?.updateOne({ students })
      return res.json({ success: true, result })
    } catch (error) {
      console.error(error)
      return res.status(500).json({ success: false, message: 'Something went wrong.' })
    }
  },
  rollCallByImage: async (req: Request, res: Response) => {
    console.log('POST to rollCallByImage.')

    try {
      const file = req.files?.image
      const course = JSON.parse(req.body?.course as unknown as string) as TCourse

      if (file === undefined || Array.isArray(file)) {
        const message = 'No file was uploaded or too many files were uploaded.'
        return res.status(400).send({ success: false, message })
      }
      // const fileURL = `${process.env.HOST ?? 'http://localhost'}:${process.env.PORT ?? '8000'}/uploads/${fileName}`

      const fileName = v4() + '-' + file?.name
      const dirPath = path.join(rootPath, 'public', 'static', 'roll_call_original')
      const uploadPath = path.join(dirPath, fileName)
      if (!existsSync(dirPath)) mkdirSync(dirPath, { recursive: true })

      file.mv(uploadPath, async (err) => {
        try {
          if (err !== undefined) {
            return res.status(500).send({ success: false, message: 'Something went wrong.' })
          } else {
            const dateTime = new Date()

            const URL = `${process.env.PYTHON_HOST ?? 'http://localhost:8001'}`
            const requestBody = { fileName, dateTime, course }
            const response = await Axios.post(URL, requestBody)
            const recognizeResult = response.data as recognizeResponse
            // const recognizeResult: recognizeResponse = {
            //   originImageSize: { width: 100, height: 100 },
            //   peopleNumbers: 6,
            //   recognizeResults: [{
            //     _id: '65075f2c47c2465a36eaddda' as unknown as mongoose.Types.ObjectId,
            //     facePosition: { x: 0, y: 0, w: 0, h: 0 },
            //     fileName: '9f33b7a1-a72e-43b9-a40c-c573d3e60df5-035.jpg'
            //   }]
            // }

            const attendant = new Attendant({
              course: course?._id,
              attendanceMethod: 'Picture',
              attendees: recognizeResult.recognizeResults.map((recognizeResult): TAttendance['attendees'][0] =>
                ({ attendee: recognizeResult._id, checkInTime: dateTime, checkInType: 'Picture', proofOfAttendance: recognizeResult.fileName })
              ),
              fileName
            })
            await attendant.save()

            const originCourse = await Course.findByIdAndUpdate(course._id, { retrain: false })
            // 將新的 ObjectId 添加到原始課程的 attendants 陣列中
            const updatedAttendants = [...(originCourse?.attendants ?? []), attendant._id]

            // 更新課程的 attendants 欄位
            await originCourse?.updateOne({ attendants: updatedAttendants })

            return res.send({ success: true })
          }
        } catch (error) {
          console.error(error)
          return res.status(500).send({ success: false, message: 'Something went wrong.' })
        }
      })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  test: async (req: Request, res: Response) => {
    try {
      console.log('GET /course/test REQUEST.')
      await Course.deleteMany({})
      const gcl = await User.findOne({ name: '李國川' })
      for (const rawCourse of coursesData) {
        const oldCourse = await Course.find({ courseID: rawCourse['開課課號'] })
        if (oldCourse.length >= 1) continue
        const course = new Course({
          courseID: rawCourse['開課課號'],
          instructor: gcl?._id,
          courseName: rawCourse['科目名稱'],
          class: rawCourse['開課班級'],
          compulsoryElective: rawCourse['必/選修'],
          uCourse: rawCourse['U課程'],
          campus: rawCourse['上課校區'],
          classTime: rawCourse['上課時間'],
          courseCode: rawCourse['科目代號'],
          openSeats: rawCourse['開放名額'],
          enrollment: rawCourse['選課人數'],
          credits: rawCourse['學分'],
          note: rawCourse['備註']
        })
        // console.log(course)
        // if (count === 1) { break }
        await course.save()
      }
      const courses = await Course.find({})

      res.json({ success: 'true', data: { courses } })
    } catch (error) {
      console.error(error)
      res.status(500).send({ success: false, message: 'err' })
    }
  }
}

// interface trainingRequest {
//   course: {
//     courseID: string
//     courseName: string
//     students: [{
//       _id: mongoose.Types.ObjectId
//       username: string
//       name: string
//     }]
//   }
// }

interface recognizeResponse {
  originImageSize: { width: number, height: number }
  peopleNumbers: number
  recognizeResults: [{
    _id: mongoose.Types.ObjectId
    facePosition: { x: number, y: number, w: number, h: number }
    fileName: string
  }]
}

export default courseController
