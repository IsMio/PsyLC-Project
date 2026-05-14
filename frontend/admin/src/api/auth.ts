import request from './request'

interface LoginParams {
  username: string
  password: string
  code?: string
}

export const login = (params: LoginParams) => {
  return request({
    url: '/auth/login',
    method: 'post',
    data: params
  })
}

export const logout = () => {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

export const getCurrentUser = () => {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}

export const register = (params: {
  username: string
  password: string
  confirmPassword: string
}) => {
  return request({
    url: '/auth/register',
    method: 'post',
    data: params
  })
}

export const sendEmailCode = (params: { username: string }) => {
  return request({
    url: '/auth/resource/email/code',
    method: 'post',
    data: params
  })
}
