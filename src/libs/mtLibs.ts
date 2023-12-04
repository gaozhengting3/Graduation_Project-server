import { existsSync, lstatSync, readdirSync, rmdirSync, unlinkSync } from 'fs'
import { unlink } from 'fs/promises'
import path from 'path'

const publicUrl = new URL(process.env.PUBLIC_URL ?? '')
const privateUrl = new URL(process.env.PRIVATE_URL ?? '')

export const FileManager = {
  deleteFile: async (filePath: string | undefined): Promise<void> => {
    try {
      if (filePath !== undefined && existsSync(filePath)) {
        await unlink(filePath)
      }
    } catch (error) {
      console.error(`delete file error: ${filePath} `, error)
      // throw error
    }
  },
  deleteFolderRecursive: function (directoryPath: string) {
    if (existsSync(directoryPath)) {
      readdirSync(directoryPath).forEach((file, index) => {
        const curPath = path.join(directoryPath, file)
        if (lstatSync(curPath).isDirectory()) {
          // recurse
          this.deleteFolderRecursive(curPath)
        } else {
          // delete file
          unlinkSync(curPath)
        }
      })
      rmdirSync(directoryPath)
    }
  }
}
export const UrlParser = {
  toPublic: (url: string | undefined) => {
    // console.log('url', url)
    if (url === undefined || url === '') { return '' }
    const parsedUrl = url.replace(new URL(url).origin, publicUrl.origin)
    return parsedUrl
  },
  toPrivate: (url: string | undefined) => {
    // console.log('url', url)
    if (url === undefined || url === '') { return '' }
    const parsedUrl = url.replace(new URL(url).origin, privateUrl.origin)
    return parsedUrl
  }
}
