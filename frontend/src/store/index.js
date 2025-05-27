import { createStore } from 'vuex'

export default createStore({
  state: {
    token: '',
    user: {},
    sidebar: {
      opened: true
    }
  },
  getters: {
    token: state => state.token,
    user: state => state.user,
    sidebar: state => state.sidebar
  },
  mutations: {
    setToken(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },
    setUser(state, user) {
      state.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    clearUserInfo(state) {
      state.token = ''
      state.user = {}
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    toggleSidebar(state) {
      state.sidebar.opened = !state.sidebar.opened
    }
  },
  actions: {
    login({ commit }, data) {
      return new Promise((resolve, reject) => {
        this._vm.$http.post('/login', data)
          .then(res => {
            const { success, token, user } = res.data
            if (success) {
              commit('setToken', token)
              commit('setUser', user)
              resolve(res.data)
            } else {
              reject(new Error('登录失败'))
            }
          })
          .catch(err => {
            reject(err)
          })
      })
    },
    logout({ commit }) {
      return new Promise(resolve => {
        commit('clearUserInfo')
        resolve()
      })
    },
    register({ commit }, data) {
      return new Promise((resolve, reject) => {
        this._vm.$http.post('/register', data)
          .then(res => {
            const { success, token, user } = res.data
            if (success) {
              commit('setToken', token)
              commit('setUser', user)
              resolve(res.data)
            } else {
              reject(new Error('注册失败'))
            }
          })
          .catch(err => {
            reject(err)
          })
      })
    }
  },
  modules: {
  }
}) 