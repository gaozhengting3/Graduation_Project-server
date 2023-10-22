import attendantController from '@/controllers/attendantController'
import { Router } from 'express'

const router = Router()
router.delete('/:attendantID', attendantController.deleteAttendantsById)
router.get('/course/:courseID', attendantController.getAttendantsByCourse)
router.put('/attendees/:attendantID', attendantController.updateAttendeesById)

export default router
