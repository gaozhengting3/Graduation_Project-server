import attendantController from '@/controllers/attendantController'
import { Router } from 'express'

const router = Router()
router.delete('/:attendantID', attendantController.deleteAttendantById)
router.put('/:attendantID', attendantController.updateAttendantById)
router.get('/course/:courseID', attendantController.getAttendantsByCourse)
router.put('/absentees/:attendantID', attendantController.updateAbsenteesById)

export default router
