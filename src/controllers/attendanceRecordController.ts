import { FileManager, UrlParser } from '@/libs/mtLibs'
import { fileNameToURL } from '@/libs/uploader'
import AttendanceRecord, { type TAttendanceRecord } from '@/models/AttendanceRecord'
import Attendant, { type TAttendant } from '@/models/Attendant'
import Course, { type TCourse } from '@/models/Course'
import axios from 'axios'
import { type Request, type Response } from 'express'
import FormData from 'form-data'
import { existsSync, mkdirSync } from 'fs'
import type mongoose from 'mongoose'
import path from 'path'
import { v4 } from 'uuid'

const rootPath = path.dirname(path.dirname(__dirname))
const attendanceRecordsPath = path.join(rootPath, 'public', 'static', 'attendance_records')

const attendanceRecordController = {
  get_attendanceRecord_by_courseID: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      if (courseID === undefined || courseID === '') { return res.status(400).json({ success: false, message: 'Invalid or missing Course ID.' }) }
      const course = await Course.findOne({ courseID })
      if (course === null) { return res.status(404).json({ success: false, message: 'Course not found.' }) }
      const attendanceRecords = await AttendanceRecord.find({ course: course?._id }).populate({ path: 'attendant', populate: [{ path: 'absentees.user' }, { path: 'attendees.user' }] })
      attendanceRecords.forEach((attendanceRecord) => {
        (attendanceRecord.attendant as unknown as TAttendant)?.attendees
          .forEach(attendee => { attendee.proofOfAttendance = UrlParser.toPublic(attendee.proofOfAttendance) })
      })
      return res.json({ success: true, data: { attendanceRecords: attendanceRecords.reverse() } })
    } catch (error) {
      console.error(error)
      return res.status(500).json({ success: false, message: 'Internal Server Error.' })
    }
  },
  create_attendanceRecord_by_courseID: async (req: Request, res: Response) => {
    console.log('POST to create attendance-record')
    try {
      const { courseID, createAttendant, settings: settingsFromBody } = req.body as { courseID: string, createAttendant: boolean, settings: string }
      const settings = JSON.parse(settingsFromBody) as TAttendanceRecord['settings']
      const file = req.files?.image
      const course = await Course.findOne({ courseID })
      if (course === undefined || course === null) { return res.status(400).json({ success: false, message: 'Invalid or missing Course ID.' }) }
      if (file === undefined || Array.isArray(file)) { return res.status(400).send({ success: false, message: 'No file was uploaded or too many files were uploaded.' }) }
      if (createAttendant) {
        const formData = new FormData()
        formData.append('image', file.data)
        const attendanceRecord = new AttendanceRecord({ course: course?._id, settings })
        // console.log(' [debug] settings: ', typeof settings)
        // console.log(' [debug] settings["lateSeconds"]: ', settings.lateSeconds)
        // console.log(' [debug] settings.lateSeconds: ', settings.lateSeconds)
        // console.log(' [debug] attendanceRecord: ', attendanceRecord)
        // attendanceRecord.settings.lateSeconds = settings.lateSeconds
        const save = await attendanceRecord.save()
        console.log(' [debug] save attendanceRecord: ', save)
        const updatedAttendanceRecords = [...(course?.attendanceRecords ?? []), attendanceRecord._id]
        await course?.updateOne({ attendanceRecords: updatedAttendanceRecords })

        const responseDate = await axios.post(`${process.env.HOST}:${process.env.PORT}/api/course/roll-call/image/${courseID}`, formData, { headers: { Authorization: process.env.AUTH_TOKEN } })
        const { data: { attendant: attendantID } } = responseDate.data
        await attendanceRecord.updateOne({ attendant: attendantID })
        return res.json({ success: true, data: { attendanceRecord }, message: 'Attendance record created successfully.' })
      }
    } catch (error) {
      console.error(error)
      return res.status(500).json({ success: false, message: 'Internal Server Error.' })
    }
  },
  update_attendanceRecord_by_id: async (req: Request, res: Response) => {
    try {
      const { id } = req.params
      const { courseID, updateType } = req.body
      const attendanceRecord = await AttendanceRecord.findById(id).populate('course').populate('attendant')

      const pathName = path.join(rootPath, 'private', 'attendance-records', courseID, id)

      if (attendanceRecord === null || attendanceRecord === undefined) return res.status(404).json({ success: false, message: 'No attendance record found.' })
      if (updateType === 'insert') {
        // console.log('PUT to insert, photoNumbers: ', photoNumbers)
        let files = req.files?.image
        if (files === undefined) { return res.status(400).send({ success: false, message: 'No file was uploaded or too many files were uploaded.' }) }
        if (!Array.isArray(files)) { files = [files] }
        // console.log(' ![debug] image:', files.length)

        const uploadFrames = []
        if (!existsSync(pathName)) mkdirSync(pathName, { recursive: true })

        for (const file of files) {
          const fileName = v4() + '.jpg'
          const uploadPath = path.join(pathName, fileName)
          try {
            await file.mv(uploadPath)
            const dateTime = file.name === 'media' ? new Date() : new Date(file.name)
            uploadFrames.push({ fileName, dateTime })
          } catch (error) {}
        }

        const updateFrames = [...(attendanceRecord?.frames ?? []), ...uploadFrames]
        await attendanceRecord?.updateOne({ frames: updateFrames })
        return res.send({ success: true, message: 'Frame upload success.', data: { attendanceRecord: attendanceRecord?._id } })
      }

      if (updateType === 'detect') {
        console.log('PUT to detect! ')
        try {
          if (!attendanceRecord.detected && !attendanceRecord.detecting) {
            const deletePath: string[] = []
            const requestData = { pathName, frames: attendanceRecord.frames, startTime: attendanceRecord.startTime, course: attendanceRecord.course, settings: attendanceRecord.settings }
            await attendanceRecord.updateOne({ detecting: true })
            const response = await axios.post(`${process.env.PYTHON_HOST ?? 'http://localhost:8001'}/detect`, requestData)
            const recognizeResponse = response.data as TRecognizeResponse
            console.log('[debug] const recognizeResponse =', JSON.stringify(recognizeResponse))
            // console.log('[debug] !recognizeResponse.frames:', recognizeResponse.frames)
            const { attendees: originAttendees } = attendanceRecord.attendant as unknown as TAttendant
            const attendees = recognizeResponse.rollCallResults?.map((rollCallResult): TAttendant['attendees'][0] => {
              const proofOfAttendance = originAttendees.find((attendee) => attendee.user.toString() === rollCallResult.user.toString())?.proofOfAttendance

              const filenames = proofOfAttendance?.split('/') ?? ['']
              deletePath.push(path.join(attendanceRecordsPath, filenames[filenames.length - 1]))
              return {
                user: rollCallResult.user,
                status: rollCallResult.status,
                checkInTime: rollCallResult.dateTime,
                checkInType: 'Picture',
                facePosition: rollCallResult.facePosition,
                proofOfAttendance: fileNameToURL(['attendance_records'], rollCallResult.fileName)
              }
            }
            ) ?? []
            for (let i = 0; i < deletePath.length; i++) {
              await FileManager.deleteFile(deletePath[i])
            }
            const { students } = attendanceRecord.course as unknown as TCourse
            const absentees = students.filter((student) => attendees.findIndex((attendee) => attendee.user.toString() === student.toString()) === -1)
              .map((student): TAttendant['absentees'][0] => ({ user: student, checkInTime: attendanceRecord.startTime }))
            await attendanceRecord.updateOne({ frames: response.data.frames, detecting: false, detected: true })
            // console.log('[debug] absentees:', absentees)
            console.log('[debug] attendees:', attendees)
            await Attendant.findByIdAndUpdate(attendanceRecord.attendant, { absentees, attendees })
            return res.send({ success: true, message: 'Detected successfully.' })
          }
          return res.send({ success: true, message: 'Already detected or on detecting.' })
        } catch (error) {
          console.log('[error] PUT detect error!', error)
          await attendanceRecord.updateOne({ detecting: false })
          throw error
        }
      }

      if (updateType === 'score') {
        console.log('PUT to scoring! ')
        const { attendees } = attendanceRecord.attendant as unknown as TAttendant
        const requestData = { pathName, frames: attendanceRecord.frames, course: attendanceRecord.course, settings: attendanceRecord.settings, attendees: attendees.map(attendee => attendee.user) }
        console.log('[debug] const requestData = ', JSON.stringify(requestData))
        const response = await axios.post(`${process.env.PYTHON_HOST ?? 'http://localhost:8001'}/judge`, requestData)
        const { statistic, scores } = response.data
        await attendanceRecord.updateOne({ statistic, scores })
        return res.send({ success: true, data: response.data })
      }
    } catch (error) {
      console.error((error))
      console.error(('[error] PUT error!'))
      return res.status(500).json({ success: false, message: 'Internal Server Error.' })
    }
  },
  delete_attendanceRecord_by_id: async (req: Request, res: Response) => {
    try {
      const { id } = req.params
      const attendanceRecord = await AttendanceRecord.findByIdAndDelete(id)
      if (attendanceRecord === undefined || attendanceRecord === null) { return res.status(404).json({ success: false, message: 'Attendant not found.' }) }

      const course = await Course.findByIdAndUpdate(attendanceRecord?.course, { $pull: { attendanceRecords: attendanceRecord._id } })
      const pathName = path.join(rootPath, 'private', 'attendance-records', course?.courseID ?? '', id)
      FileManager.deleteFolderRecursive(pathName)

      return res.status(200).json({ success: true, message: 'Attendant has been deleted successfully.' })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  update_attendanceRecord_settings_by_id: async (req: Request, res: Response) => {
    try {
      const { id } = req.params
      const { settings } = req.body
      const attendanceRecord = await AttendanceRecord.findById(id)
      await attendanceRecord?.updateOne({ settings })
      return res.json({ success: true, message: 'Settings update successfully' })
    } catch (error) {
      console.error(error)
      return res.status(500).json({ success: false, message: 'Internal Server Error.' })
    }
  }
}

export default attendanceRecordController

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
    status: string
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
