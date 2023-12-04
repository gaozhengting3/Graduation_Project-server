import { FileManager } from '@/libs/mtLibs'
import { type TAttendanceRecord } from '@/models/AttendanceRecord'
import { type TAttendant } from '@/models/Attendant'
import Course from '@/models/Course'
import User, { type TUser } from '@/models/User'
import axios from 'axios'
import { type Request, type Response } from 'express'
import { existsSync, mkdirSync } from 'fs'
import fs from 'fs/promises'
import JWT from 'jsonwebtoken'
import path from 'path'
import { v4 } from 'uuid'
const rootPath = path.dirname(path.dirname(__dirname))
const facePath = path.join(rootPath, 'private', 'users_face')

const getFaceNumbersById = async (id: string | undefined): Promise<number> => {
  if (id === undefined || id === '') return 0
  const userFolderPath = path.join(facePath, id)
  if (await fs.access(userFolderPath).then(() => true).catch(() => false)) {
    const files = await fs.readdir(userFolderPath)
    return files.length
  } else { return 0 }
}

const userController = {
  getOneById: async (req: Request, res: Response) => {
    try {
      const { id } = req.params
      const { _id: reqId } = req.user as any
      if (reqId.toString() !== id) {
        return res.status(403).json({ success: false, message: 'Your are not permitted access to the resource.' })
      }
      const user = await User.findById(reqId)
      const { _id, username, name, email, role, thumbnail } = user ?? {}
      const faceNumbers = await getFaceNumbersById(id?.toString())
      const payload = { _id, username, name, email, role, thumbnail, faceNumbers }
      return res.send({ success: true, data: { user: payload } })
    } catch (error) {
      console.error(error)
      res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  },
  getAllByRole: async (req: Request, res: Response) => {
    try {
      const { role } = req.params
      const students = await User.find({ role }).sort({ username: 1 })
      return res.status(200).json({ success: true, data: { students } })
    } catch (error) {
      return res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  },
  getStudentsByCourseId: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      const course = await Course.findOne({ courseID }).populate(['students', 'attendants', 'attendanceRecords'])
      // .populate(
      // .populate({ path: 'attendants', select: ['absentees'] })

      if (course === undefined || course === null) {
        return res.status(404).json({ success: false, error: 'Course not found.' })
      }

      // console.log(course)

      const students = course.students as unknown[] as Array<TUser & { statistics?: Statistics } >
      const attendanceRecords = course.attendanceRecords as unknown[] as TAttendanceRecord[]
      const attendants = course.attendants as unknown[] as TAttendant[]

      students.sort((a, b) => a.username.localeCompare(b.username))

      // statistics
      const studentsStatistics: Record<string, Statistics> = {}

      // initial statistics
      students.forEach(student => { studentsStatistics[student._id] = { attendanceTimes: 0, totalScore: 0, scoresCount: 0 } })
      // count attendanceTimes
      attendants.forEach(attendant => { attendant.attendees.forEach(attendee => { studentsStatistics[attendee.user.toString()].attendanceTimes += 1 }) })

      // count averageScore
      attendanceRecords.forEach(attendanceRecord => {
        attendanceRecord.scores.forEach(score => {
          studentsStatistics[score.user ?? ''].totalScore += score.score ?? 0
          studentsStatistics[score.user ?? ''].scoresCount += 1
        })
      })

      // console.log(' [debug] students: ', students)
      const statisticStudents = students.map((student) => {
        // console.log(student.name, studentsStatistics[student._id.toString()])
        const obj = JSON.parse(JSON.stringify(student)) as typeof student
        obj.statistics = studentsStatistics[student._id.toString()] ?? {}
        return obj
      })
      // console.log(' [debug] update students: ', statisticStudents)

      return res.status(200).json({ success: true, data: { students: statisticStudents } })
    } catch (error) {
      return res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  },
  insertOne: async (req: Request, res: Response) => {
    try {
      const { username, name, email, password, role, thumbnail } = req.body
      const existedUser = await User.find({ username })
      if (existedUser.length > 0) {
        return res.status(400).json({
          success: false,
          message: 'The username has already existed.'
        })
      }
      const user = new User({ username, name, email, password, role, thumbnail })
      await user.save()
      return res.status(200).json({ success: true, message: 'The user has been created successfully.' })
    } catch (error) {
      console.error(error)
      return res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  },
  signIn: async (req: Request, res: Response) => {
    try {
      const { username, password, system } = req.body
      if (typeof username === 'string' && typeof password === 'string') {
        const user = await User.findOne({ username })
        if (user !== undefined) {
          const isMatch = await user?.comparePassword(password) ?? false
          if (isMatch) {
            const { _id, username, name, email, role, thumbnail } = user ?? {}
            const faceNumbers = await getFaceNumbersById(_id?.toString())
            const payload = { _id, username, name, email, role, thumbnail, faceNumbers }

            let expiresIn = '1d'
            if (system !== undefined && system === 'mobile') expiresIn = '1y'

            const token = JWT.sign(payload, process.env.PASSPORT_SECRET ?? '', { expiresIn })
            return res.send({ success: true, token: 'JWT ' + token, user: payload })
          }
        }
        return res.status(401).json({ success: false, message: 'Username or password mismatch.' })
      }
    } catch (error) {
      console.error(error)
      res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  },
  deleteFace: async (req: Request, res: Response) => {
    try {
      const { _id } = req.user as TUser
      const dirPath = path.join(facePath, _id.toString())
      FileManager.deleteFolderRecursive(dirPath)
      return res.status(200).json({ success: true, message: 'Faces have been deleted successfully.' })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  uploadFace: async (req: Request, res: Response) => {
    try {
      const { _id } = req.user as TUser
      // if (_id.toString() !== req.params.id) return res.status(401).json({ success: false, message: 'You can only upload your own photos.' })
      const file = req.files?.image

      if (file === undefined || Array.isArray(file)) { return res.status(400).send({ success: false, message: 'No file was uploaded or too many files were uploaded.' }) }

      const fileName = v4() + '.jpg'
      const dirPath = path.join(facePath, _id.toString())
      const uploadPath = path.join(dirPath, fileName)
      if (!existsSync(dirPath)) mkdirSync(dirPath, { recursive: true })

      file.mv(uploadPath, async (err) => {
        try {
          if (err !== undefined) {
            return res.status(500).send({ success: false, message: 'Something went wrong.' })
          } else {
            return res.send({ success: true, message: 'Face Saved successfully.' })
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
  uploadFaceVideo: async (req: Request, res: Response) => {
    try {
      console.log('POST to face-video upload.')
      const { _id } = req.user as TUser
      const file = req.files?.video
      if (file === undefined || Array.isArray(file)) { return res.status(400).send({ success: false, message: 'No file was uploaded or too many files were uploaded.' }) }

      const fileName = v4() + '.mp4'
      const dirPath = path.join(rootPath, 'private', 'users_face', _id.toString())
      const uploadPath = path.join(dirPath, fileName)
      if (!existsSync(dirPath)) mkdirSync(dirPath, { recursive: true })

      await file.mv(uploadPath)
      res.send({ success: true, message: 'Face Saved successfully.' })
      axios.post(`${process.env.PYTHON_HOST ?? 'http://localhost:8001'}/video/${_id.toString()}`, { fileName }).then(async () => {
        const courses = await Course.find({ students: _id })
        for (const course of courses) { await course.updateOne({ retrain: true }) }
      }).catch(() => {})
      // file.mv(uploadPath, async (err) => {
      //   try {
      //     if (err !== undefined) {
      //       return res.status(500).send({ success: false, message: 'Something went wrong.' })
      //     } else {
      //       res.send({ success: true, message: 'Face Saved successfully.' })
      //       await axios.post(`${process.env.PYTHON_HOST ?? 'http://localhost:8001'}/video/${_id.toString()}`, { fileName })
      //       const courses = await Course.find({ students: _id })
      //       for (const course of courses) { await course.updateOne({ retrain: true }) }
      //     }
      //   } catch (error) {
      //     console.error(error)
      //     // return res.status(500).send({ success: false, message: 'Something went wrong.' })
      //   }
      // })
    } catch (error) {
      // console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  }
}
export default userController

interface Statistics { attendanceTimes: number, totalScore: number, scoresCount: number }
