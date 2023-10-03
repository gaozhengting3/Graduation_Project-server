import userController from '@/controllers/userController'
import { Router } from 'express'

const router = Router()
router.post('/', userController.insertOne)

export default router
