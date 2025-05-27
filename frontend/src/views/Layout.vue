<template>
  <div class="layout-container" :class="{'collapse': isCollapse}">
    <div class="sidebar">
      <div class="logo-container">
        <img src="../assets/logo.png" class="logo" alt="Logo" />
        <h1 v-show="!isCollapse">咸鱼自动化工具</h1>
      </div>
      <el-menu
        :collapse="isCollapse"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        :default-active="activeMenu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><el-icon-menu /></el-icon>
          <span>控制台</span>
        </el-menu-item>
        <el-sub-menu index="product">
          <template #title>
            <el-icon><el-icon-goods /></el-icon>
            <span>商品管理</span>
          </template>
          <el-menu-item index="/products">商品列表</el-menu-item>
          <el-menu-item index="/products/add">添加商品</el-menu-item>
          <el-menu-item index="/products/hot">热门商品</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/orders">
          <el-icon><el-icon-document /></el-icon>
          <span>订单管理</span>
        </el-menu-item>
        <el-sub-menu index="customer">
          <template #title>
            <el-icon><el-icon-user /></el-icon>
            <span>客户服务</span>
          </template>
          <el-menu-item index="/messages">消息管理</el-menu-item>
          <el-menu-item index="/templates">回复模板</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/tasks">
          <el-icon><el-icon-time /></el-icon>
          <span>平台任务</span>
        </el-menu-item>
        <el-sub-menu index="image">
          <template #title>
            <el-icon><el-icon-picture /></el-icon>
            <span>内容创作</span>
          </template>
          <el-menu-item index="/image/main">主图制作</el-menu-item>
          <el-menu-item index="/image/watermark">去水印</el-menu-item>
          <el-menu-item index="/materials">素材管理</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/accounts">
          <el-icon><el-icon-s-custom /></el-icon>
          <span>账号管理</span>
        </el-menu-item>
        <el-sub-menu index="analytics">
          <template #title>
            <el-icon><el-icon-data-line /></el-icon>
            <span>营销分析</span>
          </template>
          <el-menu-item index="/analytics/hot">热销商品</el-menu-item>
          <el-menu-item index="/analytics/conversion">转化率分析</el-menu-item>
          <el-menu-item index="/analytics/matrix">矩阵分析</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/qrcode">
          <el-icon><el-icon-price-tag /></el-icon>
          <span>二维码生成</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><el-icon-setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </div>
    <div class="main">
      <div class="header">
        <div class="toggle-button" @click="toggleSidebar">
          <i class="el-icon-s-fold" v-if="!isCollapse"></i>
          <i class="el-icon-s-unfold" v-else></i>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-dropdown">
              {{ username }}
              <i class="el-icon-caret-bottom"></i>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <div class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'

export default {
  name: 'Layout',
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    
    // 侧边栏折叠状态
    const isCollapse = computed(() => !store.state.sidebar.opened)
    
    // 切换侧边栏
    const toggleSidebar = () => {
      store.commit('toggleSidebar')
    }
    
    // 当前激活的菜单
    const activeMenu = computed(() => {
      return route.path
    })
    
    // 用户名
    const username = computed(() => {
      return store.state.user.username || '用户'
    })
    
    // 处理菜单命令
    const handleCommand = (command) => {
      if (command === 'logout') {
        ElMessageBox.confirm('确定要退出登录吗?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          store.dispatch('logout').then(() => {
            router.push('/login')
          })
        }).catch(() => {})
      } else if (command === 'settings') {
        router.push('/settings')
      }
    }
    
    return {
      isCollapse,
      toggleSidebar,
      activeMenu,
      username,
      handleCommand
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
}

.sidebar {
  width: 210px;
  height: 100%;
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.layout-container.collapse .sidebar {
  width: 64px;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 15px;
  color: #fff;
  background-color: #263445;
  overflow: hidden;
}

.logo {
  width: 30px;
  height: 30px;
  margin-right: 10px;
}

.logo-container h1 {
  font-size: 18px;
  font-weight: bold;
  white-space: nowrap;
  margin: 0;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
}

.toggle-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #606266;
}

.user-dropdown i {
  margin-left: 5px;
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f0f2f5;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 