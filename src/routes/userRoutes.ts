import userController from '@/controllers/userController'
import { Router } from 'express'

const router = Router()
router.post('/test', userController.test)
router.get('/role/:role', userController.getAllByRole)
router.get('/course/:courseID', userController.getStudentsByCourseId)
router.get('/:id', userController.getOneById)
router.post('/face', userController.uploadFace)
router.post('/face-video', userController.uploadFaceVideo)
router.post('/', userController.insertMany)
router.delete('/face', userController.deleteFace)

export default router
