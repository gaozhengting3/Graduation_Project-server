import { ExtractJwt, Strategy, type StrategyOptions } from 'passport-jwt'
import User, { type TUser } from '../models/UserModel'
const opts: StrategyOptions = {
  jwtFromRequest: ExtractJwt.fromAuthHeaderWithScheme('jwt'),
  secretOrKey: process.env.PASSPORT_SECRET
}
const passportMiddleware = new Strategy(opts, async function (jwtPayload: TUser, done) {
  try {
    const user = await User.findOne({ _id: jwtPayload._id })
    if (user !== null) done(null, user)
    else done(null, false)
  } catch (error) {
    done(error, false)
  }
})

export { passportMiddleware }

