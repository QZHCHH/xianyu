import Vue from 'vue'
import VueRouter from 'vue-router'
import Layout from '../views/Layout.vue'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import ProductManagement from '../views/ProductManagement.vue'
import UserManagement from '../views/UserManagement.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '控制面板' }
      },
      {
        path: 'products',
        name: 'ProductManagement',
        component: ProductManagement,
        meta: { title: '商品管理', permission: 'product_view' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement,
        meta: { title: '用户管理', permission: 'user_manage' }
      },
      {
        path: 'orders',
        name: 'OrderManagement',
        component: () => import('../views/OrderManagement.vue'),
        meta: { title: '订单管理', permission: 'order_view' }
      },
      {
        path: 'accounts',
        name: 'AccountManagement',
        component: () => import('../views/AccountManagement.vue'),
        meta: { title: '账号管理', permission: 'account_manage' }
      },
      {
        path: 'customer-service',
        name: 'CustomerService',
        component: () => import('../views/CustomerService.vue'),
        meta: { title: '客户服务', permission: 'customer_reply' }
      },
      {
        path: 'content',
        name: 'ContentCreator',
        component: () => import('../views/ContentCreator.vue'),
        meta: { title: '内容创作', permission: 'content_create' }
      },
      {
        path: 'platform-tasks',
        name: 'PlatformTasks',
        component: () => import('../views/PlatformTasks.vue'),
        meta: { title: '平台任务', permission: 'product_view' }
      },
      {
        path: 'marketing',
        name: 'MarketingAnalyzer',
        component: () => import('../views/MarketingAnalyzer.vue'),
        meta: { title: '营销分析', permission: 'marketing_analyze' }
      }
    ]
  },
  {
    path: '*',
    redirect: '/'
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  
  if (requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    // 权限检查
    if (to.meta.permission) {
      const permissions = JSON.parse(localStorage.getItem('permissions') || '[]')
      if (!permissions.includes(to.meta.permission)) {
        // 如果没有权限，跳转到首页
        next('/')
        Vue.prototype.$message.error('权限不足')
        return
      }
    }
    next()
  }
})

export default router 