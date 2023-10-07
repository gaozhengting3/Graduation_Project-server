export const fileNameToURL = (paths: string[], fileName: string): string => {
  const HOST = `${process.env.HOST}:${process.env.PORT}`
  let routes = ''
  for (const path of paths) {
    routes += ('/' + path)
  }
  const URL = `${HOST}${routes}/${fileName}`
  return URL
}
