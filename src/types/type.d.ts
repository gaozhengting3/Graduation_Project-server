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
    fileName: string
  }]

} & IAttendanceRecord

interface IAttendanceRecord {
  __v?: any
  _id?: string
  course: ICourse & string
  startTime: Date
  endTime: Date
  detected: boolean
  attendant: IAttendant & string
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
