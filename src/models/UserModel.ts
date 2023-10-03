import bcrypt from 'bcrypt'
import mongoose, { type Document, type InferSchemaType } from 'mongoose'

const USER_ROLES = ['student', 'instructor', 'assistant']
const userSchema = new mongoose.Schema(
  {
    username: {
      type: String,
      required: true,
      minLength: 3,
      maxLength: 50
    },
    name: {
      type: String,
      required: true,
      minLength: 2,
      maxLength: 50
    },
    email: {
      type: String,
      required: true,
      minLength: 6,
      maxLength: 100
    },
    password: {
      type: String,
      required: true,
      minLength: 6,
      maxLength: 1024
    },
    role: {
      type: String,
      required: true,
      enum: USER_ROLES
    },
    thumbnail: {
      type: String,
      default: ''
    }
  },
  {
    methods: {
      comparePassword: async function (password: string) {
        try {
          return await bcrypt.compare(password, this.password)
        } catch (error) {
          console.log(error)
          throw error
        }
      }
    }
  }
)

userSchema.pre('save', async function (next) {
  if (this.isModified('password') || this.isNew) {
    const hash = await bcrypt.hash(this.password, 10)
    this.password = hash
  }
  next()
})
type TUser = InferSchemaType<typeof userSchema> & Document & Express.User
export type { TUser }
export default mongoose.model('User', userSchema)
