import UserModel from '@/models/UserModel'
import { type Request, type Response } from 'express'
import JWT from 'jsonwebtoken'

const userController = {
  insertOne: async (req: Request, res: Response) => {
    try {
      const { username, name, email, password, role, thumbnail } = req.body
      const existedUser = await UserModel.find({ username })
      if (existedUser.length > 0) {
        return res.status(400).json({
          success: false,
          message: 'The username has already existed.'
        })
      }
      const user = new UserModel({ username, name, email, password, role, thumbnail })
      await user.save()
      return res.status(200).json({ success: true, message: 'The user has been created successfully.' })
    } catch (error) {
      console.log(error)
      return res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  },
  signIn: async (req: Request, res: Response) => {
    try {
      const { username, password } = req.body
      if (typeof username === 'string' && typeof password === 'string') {
        const user = await UserModel.findOne({ username })
        if (user !== undefined) {
          const isMatch = await user?.comparePassword(password) ?? false
          if (isMatch) {
            const { _id, username, name, email, role, thumbnail } = user ?? {}
            const payload = { _id, username, name, email, role, thumbnail }
            const token = JWT.sign(payload, process.env.PASSPORT_SECRET ?? '', { expiresIn: '15m' })
            return res.send({ success: true, token: 'JWT ' + token, user: payload })
          }
        }
        return res.status(401).json({ success: false, message: 'Username or password mismatch.' })
      }
    } catch (error) {
      console.log(error)
      res.status(500).json({ success: false, error: 'Something went wrong.' })
    }
  }
}
export default userController
