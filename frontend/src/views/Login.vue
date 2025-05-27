<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>咸鱼自动化工具</h1>
        <p>欢迎使用咸鱼商家自动化工具平台</p>
      </div>
      <el-form :model="loginForm" :rules="loginRules" ref="loginForm" class="login-form">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" prefix-icon="el-icon-user" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" prefix-icon="el-icon-lock" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-button" @click="handleLogin">登录</el-button>
        </el-form-item>
        <div class="login-options">
          <router-link to="/register">没有账号？立即注册</router-link>
        </div>
      </el-form>
    </div>
    <div class="login-footer">
      <p>咸鱼自动化工具 &copy; {{ new Date().getFullYear() }} All Rights Reserved</p>
    </div>
  </div>
</template>

<script>
import { reactive, ref, toRefs } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'Login',
  setup() {
    const loginForm = reactive({
      username: '',
      password: ''
    })
    
    const loginRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }
    
    const loading = ref(false)
    const loginFormRef = ref(null)
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    
    const handleLogin = () => {
      loginFormRef.value.validate(valid => {
        if (valid) {
          loading.value = true
          store.dispatch('login', loginForm)
            .then(() => {
              ElMessage.success('登录成功')
              
              // 跳转到首页或者来源页面
              const redirectUrl = route.query.redirect || '/'
              router.push(redirectUrl)
            })
            .catch(err => {
              ElMessage.error(err.message || '登录失败，请检查用户名和密码')
            })
            .finally(() => {
              loading.value = false
            })
        } else {
          return false
        }
      })
    }
    
    return {
      loginForm,
      loginRules,
      loading,
      loginFormRef,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(to right, #3494e6, #ec6ead);
}

.login-box {
  width: 400px;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
  background-color: white;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  color: #666;
}

.login-form {
  margin-top: 20px;
}

.login-button {
  width: 100%;
}

.login-options {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
  font-size: 14px;
}

.login-options a {
  color: #409EFF;
  text-decoration: none;
}

.login-footer {
  margin-top: 20px;
  color: white;
  font-size: 12px;
}
</style> 