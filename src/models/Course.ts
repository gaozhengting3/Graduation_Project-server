import mongoose, { type Document, type InferSchemaType } from 'mongoose'
import { type TUser } from './User'

const courseSchema = new mongoose.Schema({
  courseID: { type: String, required: true, minLength: 5, maxLength: 20 },
  academicYear: { type: Number, required: true },
  semester: { type: Number, required: true },
  instructor: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  courseName: { type: String, required: true, minLength: 2, maxLength: 60 },
  class: { type: String, require: true },
  compulsoryElective: { type: String, required: true },
  uCourse: { type: String, default: '' },
  campus: { type: String, default: '' },
  classTime: { type: String, required: true },
  courseCode: { type: String, required: true },
  openSeats: { type: Number, required: true },
  enrollment: { type: Number, required: true },
  credits: { type: Number, required: true },
  note: { type: String, default: '' },
  students: { type: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }], default: [] },
  attendants: { type: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Attendant' }], default: [] },
  attendanceRecords: { type: [{ type: mongoose.Schema.Types.ObjectId, ref: 'AttendanceRecord' }], default: [] },
  retrain: { type: Boolean, default: true }
})

courseSchema.pre('save', async function (next) {
  if (this.isModified('students')) { this.retrain = true }
  next()
})

type TCourse = InferSchemaType<typeof courseSchema> & Document & Express.User & { students: TUser[] }
export type { TCourse }
export default mongoose.model('Course', courseSchema)
