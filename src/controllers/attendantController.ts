import Attendant from '@/models/Attendant'
import Course from '@/models/Course'
import { type Request, type Response } from 'express'

const attendantController = {
  getAttendantsByCourse: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      const course = await Course.findOne({ courseID })
      const attendants = await Attendant.find({ course: course?._id }).populate({ path: 'attendees.attendee', select: ['username', 'name', 'email'] })
      // console.log('attendants: ', attendants)
      // console.log('attendants.attendees: ', attendants[0].attendees)
      return res.status(200).json({ success: true, data: { attendants } })
    } catch (error) {
      console.log(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  }

}

export default attendantController
