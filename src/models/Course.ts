import mongoose, { type Document, type InferSchemaType } from 'mongoose'

const courseSchema = new mongoose.Schema({
  courseID: { type: String, required: true, minLength: 5, maxLength: 20 },
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
  attendants: { type: [{ type: mongoose.Schema.Types.ObjectId, ref: 'attendant' }], default: [] },
  retrain: { type: Boolean, default: true }
})

courseSchema.pre('save', async function (next) {
  if (this.isModified('students')) { this.retrain = true }
  next()
})

type TCourse = InferSchemaType<typeof courseSchema> & Document & Express.User
export type { TCourse }
export default mongoose.model('Course', courseSchema)
