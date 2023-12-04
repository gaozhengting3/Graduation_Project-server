import { FileManager, UrlParser } from '@/libs/mtLibs'
import AttendanceRecord from '@/models/AttendanceRecord'
import Attendant, { type AttendantType, type TAttendee } from '@/models/Attendant'
import Course from '@/models/Course'
import { type Request, type Response } from 'express'
import path from 'path'

const rootPath = path.dirname(path.dirname(__dirname))
const attendanceRecordsPath = path.join(rootPath, 'public', 'static', 'attendance_records')
const rollCallOriginalPath = path.join(rootPath, 'public', 'static', 'roll_call_original')

const attendantController = {
  getAttendantsByCourse: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      const course = await Course.findOne({ courseID })
      const attendants = await Attendant.find({ course: course?._id })
        .populate({ path: 'absentees.user', select: ['username', 'name', 'email'] })
        .populate({ path: 'attendees.user', select: ['username', 'name', 'email'] })

      const processedAttendants = attendants.map((attendant) => {
        attendant.attendees = attendant.attendees.map(attendee => {
          attendee.proofOfAttendance = UrlParser.toPublic(attendee.proofOfAttendance)
          return attendee
        })
        attendant.absentees = attendant.absentees.map(absentee => {
          absentee.proofOfAbsence = UrlParser.toPublic(absentee.proofOfAbsence)
          return absentee
        })
        attendant.unknowns = attendant.unknowns.map(unknown => {
          unknown.proofOfAttendance = UrlParser.toPublic(unknown.proofOfAttendance)
          return unknown
        })
        return attendant
      }).reverse()

      return res.status(200).json({ success: true, data: { attendants: processedAttendants } })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  updateAttendantById: async (req: Request, res: Response) => {
    try {
      const { attendantID } = req.params
      const { attendantType, attendee, updateAttendee }: { attendantType: AttendantType, attendee: TAttendee, updateAttendee: TAttendee & AttendantType } = req.body

      const originAttendant = await Attendant.findById(attendantID)
      if (originAttendant === undefined || originAttendant === null) { return res.status(404).json({ success: false, message: 'Attendant not found.' }) }

      if (attendantType === 'unknowns') {
        const url = UrlParser.toPrivate(attendee.proofOfAttendance)
        originAttendant.unknowns = originAttendant.unknowns.filter((originUnknown) => originUnknown.proofOfAttendance !== url)
        originAttendant.absentees = originAttendant.absentees.filter((originAbsentee) => originAbsentee.user._id.toString() !== updateAttendee.user._id.toString())
        originAttendant.attendees.push({ user: updateAttendee.user, checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: url, facePosition: updateAttendee.facePosition })
      } else if (attendantType === 'absentees') {
        originAttendant.absentees = originAttendant.absentees.filter((originAbsentee) => originAbsentee.user._id.toString() !== updateAttendee.user._id.toString())
        originAttendant.attendees.push({ user: updateAttendee.user, checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: '' })
      } else if (attendantType === 'attendees' && JSON.stringify(updateAttendee) === JSON.stringify({}) && attendee.proofOfAttendance !== '') {
        console.log('1')
        originAttendant.attendees = originAttendant.attendees.filter((originAttendee) => originAttendee.user._id.toString() !== attendee.user._id.toString())
        originAttendant.absentees.push({ user: attendee.user, checkInTime: new Date(), checkInType: 'Manual' })
        originAttendant.unknowns.push({ checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: attendee.proofOfAttendance })
      } else if (attendantType === 'attendees' && JSON.stringify(updateAttendee) === JSON.stringify({})) {
        console.log('2')
        originAttendant.attendees = originAttendant.attendees.filter((originAttendee) => originAttendee.user._id.toString() !== attendee.user._id.toString())
        originAttendant.absentees.push({ user: attendee.user, checkInTime: new Date(), checkInType: 'Manual' })
      } else if (attendantType === 'attendees') {
        console.log('3')
        originAttendant.attendees = originAttendant.attendees.filter((originAttendee) => originAttendee.user._id.toString() !== attendee.user._id.toString())
        originAttendant.attendees.push({ user: updateAttendee.user, checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: attendee.proofOfAttendance, status: updateAttendee.status })
        originAttendant.absentees = originAttendant.absentees.filter((originAbsentee) => originAbsentee.user._id.toString() !== updateAttendee.user._id.toString())
        originAttendant.absentees.push({ user: attendee.user, checkInTime: new Date(), checkInType: 'Manual' })
      } else {
        console.log('4')
      }

      await originAttendant.save()
      return res.status(200).json({ success: true, data: { attendants: originAttendant } })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  updateAbsenteesById: async (req: Request, res: Response) => {
    try {
      const { attendantID } = req.params
      const originAttendant = await Attendant.findById(attendantID)
      if (originAttendant === undefined || originAttendant === null) { return res.status(404).json({ success: false, message: 'Attendant not found.' }) }

      const { attendantType, attendee, updateAttendee } = req.body as { attendantType: AttendantType, attendee: TAttendee, updateAttendee: TAttendee }
      if (attendantType === undefined || attendee === undefined || updateAttendee === undefined) { return res.status(400).json({ success: false, message: 'No targets found.' }) }
      if (attendantType === 'absentees') {
        const index = originAttendant.absentees.findIndex((originAbsentee) => (originAbsentee.user.toString() === attendee.user._id.toString()))
        if (index !== -1) originAttendant.absentees[index] = updateAttendee
      }
      await originAttendant.save()
      return res.status(200).json({ success: true, message: 'Absentees have been updated successfully.' })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  deleteAttendantById: async (req: Request, res: Response) => {
    try {
      const { attendantID } = req.params
      console.log(attendantID)
      const attendanceRecord = await AttendanceRecord.findOne({ attendant: attendantID })
      if (attendanceRecord !== null) return res.status(400).json({ success: false, message: '此點名紀錄無法刪除，若要刪除點名請先刪除與之對應的評分紀錄' })
      const attendant = await Attendant.findByIdAndDelete(attendantID)
      if (attendant === undefined || attendant === null) { return res.status(404).json({ success: false, message: '此紀錄已被刪除.' }) }
      await Course.findByIdAndUpdate(attendant?.course, { $pull: { attendants: attendant._id } })

      await FileManager.deleteFile(path.join(rollCallOriginalPath, attendant.fileName ?? ''))
      for (const attendees of [...attendant.unknowns, ...attendant.attendees]) {
        const filenames = attendees.proofOfAttendance.split('/')
        await FileManager.deleteFile(path.join(attendanceRecordsPath, filenames[filenames.length - 1]))
      }

      return res.status(200).json({ success: true, message: 'Attendant has been deleted successfully.' })
    } catch (error) {
      console.error(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  }

}

export default attendantController
