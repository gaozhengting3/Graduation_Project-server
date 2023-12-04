import mongoose, { type Document, type InferSchemaType } from 'mongoose'

const attendanceRecordSchema = new mongoose.Schema({
  course: { type: mongoose.Schema.Types.ObjectId, ref: 'Course', required: true },
  startTime: { type: Date, required: true, default: Date.now },
  endTime: { type: Date, required: false },
  detected: { type: Boolean, default: false, require: true },
  detecting: { type: Boolean, default: false, require: true },
  attendant: { type: mongoose.Schema.Types.ObjectId, ref: 'Attendant', required: false },
  scores: {
    type: [{
      user: { type: String },
      score: { type: Number },
      disappearedTimes: { type: Number },
      eyesClosedTimes: { type: Number },
      overAngleTimes: { type: Number }
    }],
    default: []
  },
  settings: {
    type: {
      detectMode: { type: String, enum: ['retina', 'dlib'], required: true, default: 'dlib' },
      scaleFlag: { type: Boolean, default: true, required: true },
      lateSeconds: { type: Number, min: 0, max: 50 * 60, default: 0, required: true },
      weights: {
        type: {
          disappeared: { type: Number, default: 1, min: 0, max: 1, required: true },
          eyesClosed: { type: Number, default: 1, min: 0, max: 1, required: true },
          overAngle: { type: Number, default: 1, min: 0, max: 1, required: true }
        },
        default: {
          disappeared: 1,
          eyesClosed: 1,
          overAngle: 1
        },
        require: true
      },
      sensitivity: { type: Number, default: 0.7, min: 0, max: 1, required: true },
      minScore: { type: Number, default: 0, min: 0, max: 100, required: true },
      maxScore: { type: Number, default: 100, min: 0, max: 100, required: true },
      interval: { type: Number, default: 0.3, min: 0, max: 1, required: true }
    },
    require: true,
    default: {
      scaleFlag: true,
      sensitivity: 0.7,
      lateSeconds: 45,
      minScore: 0,
      maxScore: 100,
      interval: 0.25,
      weights: {
        disappeared: 1,
        eyesClosed: 1,
        overAngle: 1
      }
    }
  },
  frames: {
    type: [{
      fileName: { type: String, required: true },
      dateTime: { type: Date, required: true, default: Date.now },
      results: {
        type: [{
          user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
          result: { type: { eyesClosed: { type: Boolean }, eulerAngle: { pitch: { type: Number }, roll: { type: Number }, yaw: { type: Number } } }, required: false, default: null }
        }],
        default: []
      }
    }]
  },
  statistic: {
    type: {
      minimum: { type: Number },
      maximum: { type: Number },
      median: { type: Number },
      average: { type: Number },
      mode: { type: Number }
    },
    require: false
  }
})

export type TAttendanceRecord = InferSchemaType<typeof attendanceRecordSchema> & Document
export default mongoose.model('AttendanceRecord', attendanceRecordSchema)
