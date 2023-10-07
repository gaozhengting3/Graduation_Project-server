import { fileNameToURL } from '@/libs/uploader'
import mongoose, { type Document, type InferSchemaType } from 'mongoose'

const attendanceMethods = ['QR Code', 'Picture', 'Manual', 'Other']

const attendantSchema = new mongoose.Schema({
  course: { type: mongoose.Schema.Types.ObjectId, ref: 'Course', required: true },
  time: { type: Date, required: true, default: new Date() },
  attendanceMethod: { type: String, enum: attendanceMethods, required: true },
  attendees: {
    type: [
      {
        attendee: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
        checkInTime: { type: Date, required: true, default: new Date() },
        checkInType: { type: String, required: true, enum: attendanceMethods },
        proofOfAttendance: { type: String, default: '' },
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
  }
  next()
})

type TAttendance = InferSchemaType<typeof attendantSchema> & Document & Express.User

export type { TAttendance }
export default mongoose.model('Attendant', attendantSchema)
