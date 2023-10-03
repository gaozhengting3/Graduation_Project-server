import userController from '@/controllers/userController'
import { Router } from 'express'

const router = Router()
router.post('/signin', userController.signIn)

export default router
