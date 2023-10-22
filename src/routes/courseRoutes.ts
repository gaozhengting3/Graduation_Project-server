import courseController from '@/controllers/courseController'
import { Router } from 'express'

const router = Router()
// router.get('/', courseController.getCourse)
router.get('/test', courseController.test)

router.get('/instructor/:instructor', courseController.getCoursesByInstructor)
router.get('/student/:student', courseController.getCoursesByStudent)
router.get('/:courseID', courseController.getCourseById)

router.post('/roll-call/image', courseController.rollCallByImage)

router.put('/:courseID/students', courseController.updateCourseStudents)

export default router
