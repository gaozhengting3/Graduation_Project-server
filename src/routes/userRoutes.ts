import userController from '@/controllers/userController'
import { Router } from 'express'

const router = Router()
router.get('/role/:role', userController.getAllByRole)
router.post('/', userController.insertOne)

export default router
