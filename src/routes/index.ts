import { passportMiddleware } from '@/configs/passport'
import attendantRouter from '@/routes/attendantRoutes'
import authRouter from '@/routes/authRoutes'
import courseRouter from '@/routes/courseRoutes'
import userRouter from '@/routes/userRoutes'
import { Router, type Express } from 'express'
import passport from 'passport'

passport.use(passportMiddleware)

const APIRouter = Router()
APIRouter.use('/course', courseRouter)
APIRouter.use('/user', userRouter)
APIRouter.use('/attendant', attendantRouter)

export default function useRoutes (app: Express): void {
  // app.use('/api', APIRouter)
  app.use('/api', passport.authenticate('jwt', { session: false }), APIRouter)
  app.use('/auth', authRouter)
}
