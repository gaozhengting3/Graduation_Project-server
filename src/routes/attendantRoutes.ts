import attendantController from '@/controllers/attendantController'
import { Router } from 'express'

const router = Router()
router.get('/course/:courseID', attendantController.getAttendantsByCourse)

export default router
