import courseController from '@/controllers/courseController'
import { Router } from 'express'

const router = Router()
// router.get('/', courseController.getCourse)
router.get('/test', courseController.test)

router.get('/instructor/:instructor', courseController.getCoursesByInstructor)
router.get('/:courseID', courseController.getCourseByID)

router.post('/roll-call/image', courseController.rollCallByImage)

router.put('/:courseID/students', courseController.updateCourseStudents)

export default router
