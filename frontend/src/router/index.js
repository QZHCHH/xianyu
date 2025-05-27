import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '控制台', requireAuth: true }
      },
      {
        path: '/products',
        name: 'Products',
        component: () => import('../views/products/ProductList.vue'),
        meta: { title: '商品管理', requireAuth: true }
      },
      {
        path: '/products/add',
        name: 'AddProduct',
        component: () => import('../views/products/AddProduct.vue'),
        meta: { title: '添加商品', requireAuth: true }
      },
      {
        path: '/products/edit/:id',
        name: 'EditProduct',
        component: () => import('../views/products/EditProduct.vue'),
        meta: { title: '编辑商品', requireAuth: true }
      },
      {
        path: '/products/hot',
        name: 'HotProducts',
        component: () => import('../views/products/HotProducts.vue'),
        meta: { title: '热门商品', requireAuth: true }
      },
      {
        path: '/orders',
        name: 'Orders',
        component: () => import('../views/orders/OrderList.vue'),
        meta: { title: '订单管理', requireAuth: true }
      },
      {
        path: '/qrcode',
        name: 'QRCode',
        component: () => import('../views/tools/QRCode.vue'),
        meta: { title: '二维码生成', requireAuth: true }
      },
      {
        path: '/customers',
        name: 'Customers',
        component: () => import('../views/customers/CustomerList.vue'),
        meta: { title: '客户管理', requireAuth: true }
      },
      {
        path: '/messages',
        name: 'Messages',
        component: () => import('../views/customers/MessageList.vue'),
        meta: { title: '消息管理', requireAuth: true }
      },
      {
        path: '/templates',
        name: 'Templates',
        component: () => import('../views/templates/TemplateList.vue'),
        meta: { title: '模板管理', requireAuth: true }
      },
      {
        path: '/tasks',
        name: 'Tasks',
        component: () => import('../views/tasks/TaskList.vue'),
        meta: { title: '平台任务', requireAuth: true }
      },
      {
        path: '/image/main',
        name: 'MainImage',
        component: () => import('../views/image/MainImage.vue'),
        meta: { title: '主图制作', requireAuth: true }
      },
      {
        path: '/image/watermark',
        name: 'Watermark',
        component: () => import('../views/image/Watermark.vue'),
        meta: { title: '去水印', requireAuth: true }
      },
      {
        path: '/materials',
        name: 'Materials',
        component: () => import('../views/materials/MaterialList.vue'),
        meta: { title: '素材管理', requireAuth: true }
      },
      {
        path: '/accounts',
        name: 'Accounts',
        component: () => import('../views/accounts/AccountList.vue'),
        meta: { title: '账号管理', requireAuth: true }
      },
      {
        path: '/analytics/hot',
        name: 'HotAnalytics',
        component: () => import('../views/analytics/HotAnalytics.vue'),
        meta: { title: '热销商品分析', requireAuth: true }
      },
      {
        path: '/analytics/conversion',
        name: 'ConversionAnalytics',
        component: () => import('../views/analytics/ConversionAnalytics.vue'),
        meta: { title: '转化率分析', requireAuth: true }
      },
      {
        path: '/analytics/matrix',
        name: 'MatrixAnalytics',
        component: () => import('../views/analytics/MatrixAnalytics.vue'),
        meta: { title: '矩阵分析', requireAuth: true }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('../views/settings/Settings.vue'),
        meta: { title: '系统设置', requireAuth: true }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 全局导航守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 咸鱼自动化工具` : '咸鱼自动化工具'
  
  // 检查是否需要登录权限
  if (to.matched.some(record => record.meta.requireAuth)) {
    const token = localStorage.getItem('token')
    if (!token) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router 