import mongoose from 'mongoose'

const attendanceMethods = ['QR Code', 'Biometric', 'Manual', 'Other']

const AttendanceSchema = new mongoose.Schema({
  courseID: { type: mongoose.Schema.Types.ObjectId, ref: 'Course', required: true },
  time: { type: Date, required: true },
  attendanceMethod: { type: String, enum: attendanceMethods, required: true },
  attendees: {
    type: [
      {
        attendee: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
        checkInTime: { type: Date, required: true },
        checkInType: { type: String, required: true, default: 'auto' },
        proofOfAttendance: { type: String, default: '' },
        location: { type: String }
      }
    ],
    default: []
  }
})
export default mongoose.model('Attendance', AttendanceSchema)
