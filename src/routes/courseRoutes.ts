import courseController from '@/controllers/courseController'
import { Router } from 'express'

const router = Router()
router.get('/', courseController.getOne)
router.post('/roll-call/image', courseController.rollCallByImage)

export default router
