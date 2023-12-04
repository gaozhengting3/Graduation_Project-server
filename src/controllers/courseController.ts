import Attendant, { type TAttendant } from '@/models/Attendant'
import Course, { type TCourse } from '@/models/Course'
import User, { type TUser } from '@/models/User'
// import csv from 'async-csv'
import axios, { AxiosError } from 'axios'
import bcrypt from 'bcrypt'
import { type Request, type Response } from 'express'
import type fileUpload from 'express-fileupload'
import { existsSync, mkdirSync } from 'fs'
import { readFile } from 'fs/promises'
import type mongoose from 'mongoose'
import path from 'path'
import { v4 } from 'uuid'

const csv = require('async-csv')
const cells = require('aspose.cells')

const loadOptions = cells.LoadOptions(cells.FileFormatType.XLSX)

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
      const newCourse = new Course({ courseID, title, subtitle, description, instructor, image, goals, students })
      await newCourse.save()
      return res.status(500).json({})
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'The course has already existed.' })
    }
  },
  getCourseById: async (req: Request, res: Response) => {
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
      const courses = await Course.find({}).populate('instructor', ['username', 'name', 'email'])
      return res.status(200).json({ success: true, data: courses })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  getCoursesByInstructor: async (req: Request, res: Response) => {
    try {
      const { instructor } = req.params
      const courses = await Course.find({ instructor }).populate('instructor', ['username', 'name', 'email'])

      return res.status(200).json({ success: true, data: { courses } })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  getCoursesByStudent: async (req: Request, res: Response) => {
    try {
      const { student } = req.params
      const courses = await Course.find({ students: student }).populate('instructor', ['username', 'name', 'email'])
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
      const file = req.files?.file as fileUpload.UploadedFile
      if (file !== undefined) {
        const uploadFileName = 'students.xlsx'
        const dirPath = path.join(rootPath, 'private', 'courses', courseID)
        const uploadPath = path.join(dirPath, uploadFileName)
        if (!existsSync(dirPath)) mkdirSync(dirPath, { recursive: true })
        await file.mv(uploadPath)

        const workbook = new cells.Workbook(uploadPath, loadOptions)
        const saveFileName = 'students.csv'
        const savePath = path.join(dirPath, saveFileName)
        workbook.save(savePath, cells.SaveFormat.CSV)

        const content = await readFile(savePath, 'utf-8')
        const rows = await csv.parse(content, { relax_column_count: true })
        console.log(' [debug] rows: ', rows)
        if (courseID !== rows[1][0]) return res.status(400).json({ success: false, message: '上傳班級內容錯誤，請檢查上傳檔案' })
        const students: Array<{
          username: string
          name: string
          password: string
          email: string
          role: string
        }> = []
        for (let index = 4; index < rows.length - 1; index++) {
          const element = rows[index]
          const password = await bcrypt.hash(element[1], 10)
          students.push({ username: element[1], name: element[3], password, email: `${element[1].toLowerCase()}@o365.nuu.edu.tw`, role: 'student' })
        }
        const existedStudents = await User.find({ username: { $in: students.map(student => student.username) } })
        const insertedStudents = await User.insertMany(students.filter(student => existedStudents.findIndex(existedStudent => existedStudent.username === student.username) === -1))
        const insertedStudentIds = insertedStudents.map(student => student._id)
        const course = await Course.findOneAndUpdate({ courseID }, { students: [...insertedStudentIds, ...existedStudents.map(student => student._id)] })
        // await User.deleteMany({ })
        // console.log(' [debug] result deleteStudents: ', course)
        return res.json({ success: true })
      } else {
        const course = await Course.findOne({ courseID })
        const result = await course?.updateOne({ students })
        return res.json({ success: true, result })
      }
    } catch (error) {
      console.error(error)
      return res.status(500).json({ success: false, message: '請檢查上傳檔案是否正確.' })
    }
  },
  rollCallByImage: async (req: Request, res: Response) => {
    console.log('POST to rollCallByImage.')
    try {
      const file = req.files?.image
      const { courseID } = req.params
      const course = await Course.findOne({ courseID })
      if ((req.user as TUser).role !== 'instructor') {
        return res.status(403).json({ success: false, message: 'Your are not instructor.' })
      }
      if (course === null || course === undefined) return res.status(404).json({ success: false, message: 'No course found.' })
      if (file === undefined || Array.isArray(file)) { return res.status(400).send({ success: false, message: 'No file was uploaded or too many files were uploaded.' }) }
      const fileName = v4() + '.jpg'
      const dirPath = path.join(rootPath, 'public', 'static', 'roll_call_original')
      const uploadPath = path.join(dirPath, fileName)
      if (!existsSync(dirPath)) mkdirSync(dirPath, { recursive: true })

      file.mv(uploadPath, async (err) => {
        try {
          if (err !== undefined) {
            return res.status(500).send({ success: false, message: 'Something went wrong.' })
          } else {
            const dateTime = new Date()

            const URL = `${process.env.PYTHON_HOST ?? 'http://localhost:8001'}/roll-call`
            const requestBody = { fileName, dateTime, course }

            let response
            try {
              response = await axios.post<TRecognizeResponse>(URL, requestBody)
            } catch (err: any | AxiosError) {
              if (axios.isAxiosError(err) && err?.response?.status === 400) return res.status(400).send({ success: false, message: '還沒有任何學生上傳人臉資料!' })
              else throw err
            }
            const recognizeResponse = response.data
            const attendees = recognizeResponse.recognizeResults.map((recognizeResult): TAttendant['attendees'][0] =>
              ({ user: recognizeResult.user, checkInTime: dateTime, checkInType: 'Picture', facePosition: recognizeResult.facePosition, proofOfAttendance: recognizeResult.fileName })
            )
            const unknowns = recognizeResponse.unknowns.map((unknown): TAttendant['unknowns'][0] =>
              ({ checkInTime: dateTime, checkInType: 'Picture', facePosition: unknown.facePosition, proofOfAttendance: unknown.fileName }))

            const absentees = course.students.filter((student) => attendees.findIndex((attendee) => attendee.user.toString() === student.toString()) === -1)
              .map((student): TAttendant['absentees'][0] => ({ user: student, checkInTime: dateTime }))
            const attendant = new Attendant({ course: course?._id, attendanceMethod: 'Picture', attendees, absentees, unknowns, fileName })

            await attendant.save()

            const originCourse = await Course.findByIdAndUpdate(course._id, { retrain: false })
            const updatedAttendants = [...(originCourse?.attendants ?? []), attendant._id]
            await originCourse?.updateOne({ attendants: updatedAttendants })

            return res.send({ success: true, message: 'Roll call successfully.', data: { attendant: attendant._id } })
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

export default courseController

type TRecognizeResponse = {
  originImageSize: { width: number, height: number }
  peopleNumbers: number
  recognizeResults: [{
    user: mongoose.Types.ObjectId
    facePosition: { x: number, y: number, w: number, h: number }
    fileName: string
  }]
  unknowns: [{
    facePosition: { x: number, y: number, w: number, h: number }
    fileName: string
  }]
  rollCallResults: [{
    user: mongoose.Types.ObjectId
    dateTime: Date
    facePosition: { x: number, y: number, w: number, h: number }
    fileName: string
  }]

} & IAttendanceRecord
interface IAttendanceRecord {
  __v?: any
  _id?: string
  course: TCourse & string
  startTime: Date
  endTime: Date
  detected: boolean
  attendant: TAttendant & string
  scores: [{
    user: string
    score: number
    disappearedTimes: number
    eyesClosedTimes: number
    overAngleTimes: number
  }]
  settings: {
    scaleFlag: boolean
    weights: {
      disappeared: number
      eyesClosed: number
      overAngle: number
    }
    sensitivity: number
    minScore: number
    maxScore: number
    interval: number
  }
  frames: [{
    fileName: string
    dateTime: Date
    results: [{
      user: mongoose.Schema.Types.ObjectId
      result: { eyesClosed: boolean }
      eulerAngle: { pitch: number, roll: number, yaw: number } }
    ]
  }]

  statistic: {
    minimum: number
    maximum: number
    median: number
    average: number
    mode: number
  }
}
