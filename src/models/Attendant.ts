import { fileNameToURL } from '@/libs/uploader'
import mongoose, { type Document, type InferSchemaType } from 'mongoose'

const attendanceMethods = ['QR Code', 'Picture', 'Score', 'Manual', 'Other']

const attendantSchema = new mongoose.Schema({
  course: { type: mongoose.Schema.Types.ObjectId, ref: 'Course', required: true },
  time: { type: Date, required: true, default: Date.now },
  attendanceMethod: { type: String, enum: attendanceMethods, required: true },
  attendees: {
    type: [
      {
        user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
        checkInTime: { type: Date, required: true, default: Date.now },
        checkInType: { type: String, required: true, enum: attendanceMethods },
        facePosition: { x: Number, y: Number, w: Number, h: Number },
        status: { type: String, default: '準時', required: false },
        proofOfAttendance: { type: String, default: '' },
        location: { type: String }
      }
    ],
    default: []
  },
  absentees: {
    type: [
      {
        checkInTime: { type: Date, required: true, default: new Date() },
        checkInType: { type: String, required: false, enum: attendanceMethods },
        user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
        proofOfAbsence: { type: String, default: '', required: false },
        reasonForAbsence: { type: String, default: '缺席', required: false },
        location: { type: String }
      }
    ],
    default: []
  },
  unknowns: {
    type: [
      {
        checkInTime: { type: Date, required: true, default: new Date() },
        checkInType: { type: String, required: false, enum: attendanceMethods },
        facePosition: { x: Number, y: Number, w: Number, h: Number },
        proofOfAttendance: { type: String, default: '', required: true },
        location: { type: String }
      }
    ],
    default: []
  },
  fileName: { type: String }
})

attendantSchema.pre('save', async function (next) {
  if (this.isNew) {
    this.attendees = this.attendees.map(attendee => ({
      ...attendee,
      proofOfAttendance: fileNameToURL(['attendance_records'],
        attendee.proofOfAttendance)
    }))

    this.unknowns = this.unknowns.map(unknown => ({
      ...unknown,
      proofOfAttendance: fileNameToURL(['attendance_records'],
        unknown.proofOfAttendance)
    }))
  }
  next()
})

export type TAttendee = TAttendant['absentees'][0] & TAttendant['attendees'][0] & TAttendant['unknowns'][0]
export type TAttendant = InferSchemaType<typeof attendantSchema> & Document & Express.User
export type AttendantType = 'attendees' | 'absentees' | 'unknowns'
export default mongoose.model('Attendant', attendantSchema)
