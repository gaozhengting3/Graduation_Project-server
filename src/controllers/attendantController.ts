import Attendant, { type TAttendance } from '@/models/Attendant'
import Course from '@/models/Course'
import { type Request, type Response } from 'express'

const attendantController = {
  deleteAttendantsById: async (req: Request, res: Response) => {
    try {
      const { attendantID } = req.params
      const attendant = await Attendant.findByIdAndDelete(attendantID)
      if (attendant === undefined || attendant === null) { return res.status(404).json({ success: false, message: 'Attendant not found.' }) }
      await Course.findByIdAndUpdate(attendant?.course, { $pull: { attendants: attendant._id } })
      return res.status(200).json({ success: true, message: 'Attendant has been deleted successfully.' })
    } catch (error) {
      console.log(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  getAttendantsByCourse: async (req: Request, res: Response) => {
    try {
      const { courseID } = req.params
      const course = await Course.findOne({ courseID })
      const attendants = await Attendant.find({ course: course?._id })
        .populate({ path: 'absentees.user', select: ['username', 'name', 'email'] })
        .populate({ path: 'attendees.user', select: ['username', 'name', 'email'] })

      return res.status(200).json({ success: true, data: { attendants } })
    } catch (error) {
      console.log(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  },
  updateAttendeesById: async (req: Request, res: Response) => {
    try {
      const { attendantID } = req.params
      const { origin, originAttendee, attendee }: { origin: 'absentee' | 'unknown' | 'attendee', originAttendee: TAttendance['attendees'][0], attendee: TAttendance['attendees'][0] & TAttendance['absentees'][0] | 'unknown' | 'absentee' } = req.body

      const originAttendant = await Attendant.findById(attendantID)
      if (originAttendant === undefined || originAttendant === null) { return res.status(404).json({ success: false, message: 'Attendant not found.' }) }
      if (attendee === 'unknown') {
        originAttendant.attendees = originAttendant.attendees.filter((attendee) => attendee.user._id.toString() !== originAttendee.user._id.toString())
        console.log(originAttendant.attendees)
        originAttendant.absentees.push(
          { user: originAttendee.user, checkInTime: new Date(), checkInType: 'Manual' }
        )
        originAttendant.unknowns.push(
          { checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: originAttendee.proofOfAttendance }
        )
      } else if (attendee === 'absentee') {
        originAttendant.attendees = originAttendant.attendees.filter((attendee) => attendee.user._id.toString() !== originAttendee.user._id.toString())
        console.log(originAttendant.attendees)
        originAttendant.absentees.push(
          { user: originAttendee.user, checkInTime: new Date(), checkInType: 'Manual' }
        )
        originAttendant.absentees.push(
          { user: originAttendee.user, checkInTime: new Date(), checkInType: 'Manual' }
        )
      } else if (origin === 'absentee') {
        originAttendant.absentees = originAttendant.absentees.filter((absentee) => absentee.user._id.toString() !== attendee.user._id.toString())
        originAttendant.attendees.push(
          { user: attendee.user, checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: '' }
        )
      } else if (origin === 'attendee') {
        // const attendant = await Attendant.findByIdAndUpdate(attendantID, { $pull: { attendees: { _id: originAttendee.user } }, $push: { absentees: { _id: attendee.user } } })
        originAttendant.attendees = originAttendant.attendees.filter((attendee) => attendee.user._id.toString() !== originAttendee.user._id.toString())
        originAttendant.attendees.push(
          { user: attendee.user, checkInTime: new Date(), checkInType: 'Manual', proofOfAttendance: originAttendee.proofOfAttendance }
        )
        originAttendant.absentees = originAttendant.absentees.filter((absentee) => absentee.user._id.toString() !== attendee.user._id.toString())
        originAttendant.absentees.push(
          { user: originAttendee.user, checkInTime: new Date(), checkInType: 'Manual' }
        )
      }

      await originAttendant.save()
      return res.status(200).json({ success: true, data: { attendants: originAttendant } })
    } catch (error) {
      console.log(error)
      return res.status(500).send({ success: false, message: 'Something went wrong.' })
    }
  }

}

export default attendantController
