import mongoose from 'mongoose'
const courseSchema = new mongoose.Schema({
  courseID: {
    type: String,
    required: true,
    minLength: 5,
    maxLength: 20
  },
  instructor: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  courseName: {
    type: String,
    required: true,
    minLength: 2,
    maxLength: 60
  },
  class: {
    type: String,
    require: true
  },
  compulsoryElective: {
    type: String,
    required: true
  },
  uCourse: {
    type: String,
    required: true
  },
  campus: {
    type: String,
    required: true
  },
  classTime: {
    type: String,
    required: true
  },
  courseCode: {
    type: String,
    required: true
  },
  openSeats: {
    type: Number,
    required: true
  },
  enrollment: {
    type: Number,
    required: true
  },
  credits: {
    type: Number,
    required: true
  },
  note: {
    type: String,
    required: true,
    default: ''

  },
  students: {
    type: [{
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    }],
    default: []
  },
  attendance: {
    type: [{
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Attendance'
    }],
    default: []
  }
})

export default mongoose.model('Course', courseSchema)
