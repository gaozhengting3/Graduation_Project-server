import attendanceRecordController from '@/controllers/attendanceRecordController'
import { Router } from 'express'

const router = Router()

router.get('/course/:courseID', attendanceRecordController.get_attendanceRecord_by_courseID)
router.put('/:id', attendanceRecordController.update_attendanceRecord_by_id)
router.put('/setting/:id', attendanceRecordController.update_attendanceRecord_settings_by_id)
router.delete('/:id', attendanceRecordController.delete_attendanceRecord_by_id)
router.post('/', attendanceRecordController.create_attendanceRecord_by_courseID)

export default router
