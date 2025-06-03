<template>
  <div class="user-management">
    <h1>用户管理</h1>
    
    <el-tabs v-model="activeTab" @tab-click="handleTabClick">
      <el-tab-pane label="用户列表" name="users">
        <div class="toolbar">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-input
                placeholder="搜索用户名/邮箱"
                v-model="searchQuery"
                clearable
                prefix-icon="el-icon-search">
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-select v-model="roleFilter" placeholder="角色筛选" clearable>
                <el-option
                  v-for="role in roles"
                  :key="role.value"
                  :label="role.label"
                  :value="role.value">
                </el-option>
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="statusFilter" placeholder="状态筛选" clearable>
                <el-option
                  v-for="status in statuses"
                  :key="status.value"
                  :label="status.label"
                  :value="status.value">
                </el-option>
              </el-select>
            </el-col>
            <el-col :span="6" style="text-align: right;">
              <el-button type="primary" icon="el-icon-plus" @click="showAddUserDialog">添加用户</el-button>
            </el-col>
          </el-row>
        </div>
        
        <el-table
          :data="filteredUsers"
          style="width: 100%"
          v-loading="loading">
          <el-table-column
            prop="username"
            label="用户名"
            width="180">
          </el-table-column>
          <el-table-column
            prop="email"
            label="邮箱"
            width="220">
          </el-table-column>
          <el-table-column
            prop="role"
            label="角色"
            width="120">
            <template slot-scope="scope">
              <el-tag :type="getRoleTagType(scope.row.role)">{{ getRoleText(scope.row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="status"
            label="状态"
            width="100">
            <template slot-scope="scope">
              <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
                {{ scope.row.status === 'active' ? '正常' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="created_at"
            label="创建时间"
            width="180">
            <template slot-scope="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="last_login"
            label="最后登录"
            width="180">
            <template slot-scope="scope">
              {{ scope.row.last_login ? formatDate(scope.row.last_login) : '从未登录' }}
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="250">
            <template slot-scope="scope">
              <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
              <el-button 
                size="mini" 
                :type="scope.row.status === 'active' ? 'warning' : 'success'"
                @click="handleToggleStatus(scope.row)">
                {{ scope.row.status === 'active' ? '禁用' : '启用' }}
              </el-button>
              <el-button 
                size="mini" 
                type="danger" 
                @click="handleDelete(scope.row)"
                :disabled="scope.row.username === currentUsername">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :current-page="currentPage"
            :page-sizes="[10, 20, 50, 100]"
            :page-size="pageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="totalUsers">
          </el-pagination>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="角色权限" name="roles">
        <el-table
          :data="rolesList"
          style="width: 100%">
          <el-table-column
            prop="name"
            label="角色名称"
            width="180">
          </el-table-column>
          <el-table-column
            prop="description"
            label="描述"
            width="220">
          </el-table-column>
          <el-table-column
            label="权限">
            <template slot-scope="scope">
              <el-tag
                v-for="permission in scope.row.permissions"
                :key="permission"
                size="small"
                style="margin-right: 5px; margin-bottom: 5px;">
                {{ getPermissionText(permission) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="操作日志" name="logs">
        <div class="toolbar">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-input
                placeholder="搜索用户名"
                v-model="logUsername"
                clearable
                prefix-icon="el-icon-search">
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-select v-model="logActionType" placeholder="操作类型" clearable>
                <el-option
                  v-for="action in actionTypes"
                  :key="action.value"
                  :label="action.label"
                  :value="action.value">
                </el-option>
              </el-select>
            </el-col>
            <el-col :span="12">
              <el-date-picker
                v-model="logDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%;">
              </el-date-picker>
            </el-col>
          </el-row>
          <el-row style="margin-top: 10px;">
            <el-col :span="24" style="text-align: right;">
              <el-button type="primary" @click="fetchLogs">查询</el-button>
              <el-button @click="resetLogFilters">重置</el-button>
            </el-col>
          </el-row>
        </div>
        
        <el-table
          :data="logs"
          style="width: 100%"
          v-loading="logsLoading">
          <el-table-column
            prop="username"
            label="用户名"
            width="120">
          </el-table-column>
          <el-table-column
            prop="action_type"
            label="操作类型"
            width="120">
          </el-table-column>
          <el-table-column
            prop="target_type"
            label="目标类型"
            width="120">
          </el-table-column>
          <el-table-column
            prop="target_id"
            label="目标ID"
            width="220">
          </el-table-column>
          <el-table-column
            prop="status"
            label="状态"
            width="100">
            <template slot-scope="scope">
              <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="timestamp"
            label="时间"
            width="180">
            <template slot-scope="scope">
              {{ formatDate(scope.row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="ip_address"
            label="IP地址"
            width="140">
          </el-table-column>
          <el-table-column
            label="详情">
            <template slot-scope="scope">
              <el-button 
                size="mini" 
                type="text" 
                @click="showLogDetails(scope.row)"
                v-if="scope.row.details">
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
            @size-change="handleLogSizeChange"
            @current-change="handleLogCurrentChange"
            :current-page="logCurrentPage"
            :page-sizes="[10, 20, 50, 100]"
            :page-size="logPageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="totalLogs">
          </el-pagination>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 添加/编辑用户对话框 -->
    <el-dialog :title="dialogTitle" :visible.sync="userDialogVisible" width="40%">
      <el-form :model="userForm" :rules="userRules" ref="userForm" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="isEdit"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="userForm.password" type="password"></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="!isEdit">
          <el-input v-model="userForm.confirmPassword" type="password"></el-input>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option
              v-for="role in roles"
              :key="role.value"
              :label="role.label"
              :value="role.value">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="userForm.status"
            active-value="active"
            inactive-value="disabled"
            active-text="正常"
            inactive-text="禁用">
          </el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="userDialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitUserForm">确 定</el-button>
      </div>
    </el-dialog>
    
    <!-- 日志详情对话框 -->
    <el-dialog title="日志详情" :visible.sync="logDetailsVisible" width="50%">
      <pre class="log-details">{{ logDetailsJson }}</pre>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'UserManagement',
  data() {
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'));
      } else {
        if (this.userForm.confirmPassword !== '') {
          this.$refs.userForm.validateField('confirmPassword');
        }
        callback();
      }
    };
    const validatePass2 = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'));
      } else if (value !== this.userForm.password) {
        callback(new Error('两次输入密码不一致!'));
      } else {
        callback();
      }
    };
    
    return {
      activeTab: 'users',
      searchQuery: '',
      roleFilter: '',
      statusFilter: '',
      users: [],
      filteredUsers: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      totalUsers: 0,
      
      // 角色与权限
      roles: [
        { value: 'admin', label: '管理员' },
        { value: 'manager', label: '经理' },
        { value: 'operator', label: '操作员' },
        { value: 'viewer', label: '查看者' }
      ],
      statuses: [
        { value: 'active', label: '正常' },
        { value: 'disabled', label: '禁用' }
      ],
      rolesList: [
        {
          name: '管理员',
          value: 'admin',
          description: '系统管理员，拥有所有权限',
          permissions: [
            'user_manage', 'role_manage', 'system_config',
            'log_view', 'all_accounts_view', 'all_products_view',
            'all_orders_view', 'all_data_export'
          ]
        },
        {
          name: '经理',
          value: 'manager',
          description: '部门经理，管理产品和订单',
          permissions: [
            'product_manage', 'order_manage', 'account_manage',
            'marketing_analyze', 'data_export', 'customer_service'
          ]
        },
        {
          name: '操作员',
          value: 'operator',
          description: '日常操作人员',
          permissions: [
            'product_view', 'product_edit', 'order_process',
            'customer_reply', 'content_create'
          ]
        },
        {
          name: '查看者',
          value: 'viewer',
          description: '只有查看权限',
          permissions: [
            'product_view', 'order_view', 'stats_view'
          ]
        }
      ],
      permissionMap: {
        'user_manage': '用户管理',
        'role_manage': '角色管理',
        'system_config': '系统配置',
        'log_view': '日志查看',
        'all_accounts_view': '所有账号查看',
        'all_products_view': '所有商品查看',
        'all_orders_view': '所有订单查看',
        'all_data_export': '所有数据导出',
        'product_manage': '商品管理',
        'order_manage': '订单管理',
        'account_manage': '账号管理',
        'marketing_analyze': '营销分析',
        'data_export': '数据导出',
        'customer_service': '客户服务',
        'product_view': '商品查看',
        'product_edit': '商品编辑',
        'order_process': '订单处理',
        'customer_reply': '客户回复',
        'content_create': '内容创建',
        'order_view': '订单查看',
        'stats_view': '统计查看'
      },
      
      // 用户表单
      userDialogVisible: false,
      dialogTitle: '添加用户',
      isEdit: false,
      userForm: {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'viewer',
        status: 'active'
      },
      userRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        password: [
          { validator: validatePass, trigger: 'blur' }
        ],
        confirmPassword: [
          { validator: validatePass2, trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ]
      },
      
      // 日志查询
      logs: [],
      logsLoading: false,
      logUsername: '',
      logActionType: '',
      logDateRange: [],
      logCurrentPage: 1,
      logPageSize: 10,
      totalLogs: 0,
      actionTypes: [
        { value: 'login', label: '登录' },
        { value: 'login_failed', label: '登录失败' },
        { value: 'register', label: '注册' },
        { value: 'add', label: '添加' },
        { value: 'update', label: '更新' },
        { value: 'delete', label: '删除' },
        { value: 'view', label: '查看' },
        { value: 'import', label: '导入' },
        { value: 'export', label: '导出' },
        { value: 'publish', label: '发布' },
        { value: 'password_change', label: '修改密码' },
        { value: 'role_change', label: '修改角色' }
      ],
      
      // 日志详情
      logDetailsVisible: false,
      logDetails: null,
      
      // 当前用户
      currentUsername: ''
    };
  },
  computed: {
    logDetailsJson() {
      return this.logDetails ? JSON.stringify(this.logDetails, null, 2) : '';
    }
  },
  created() {
    this.fetchUsers();
    this.currentUsername = localStorage.getItem('username');
  },
  methods: {
    fetchUsers() {
      this.loading = true;
      
      let params = {
        page: this.currentPage,
        limit: this.pageSize
      };
      
      if (this.roleFilter) {
        params.role = this.roleFilter;
      }
      
      if (this.statusFilter) {
        params.status = this.statusFilter;
      }
      
      this.$axios.get('/api/users', { params })
        .then(response => {
          if (response.data.success) {
            this.users = response.data.users;
            this.totalUsers = response.data.total || this.users.length;
            this.applyFilters();
          } else {
            this.$message.error(response.data.message || '获取用户列表失败');
          }
        })
        .catch(error => {
          this.$message.error('获取用户列表失败: ' + error.message);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    
    applyFilters() {
      if (!this.searchQuery) {
        this.filteredUsers = this.users;
        return;
      }
      
      const query = this.searchQuery.toLowerCase();
      this.filteredUsers = this.users.filter(user => {
        return user.username.toLowerCase().includes(query) || 
               (user.email && user.email.toLowerCase().includes(query));
      });
    },
    
    handleTabClick() {
      if (this.activeTab === 'users') {
        this.fetchUsers();
      } else if (this.activeTab === 'logs') {
        this.fetchLogs();
      }
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
      this.fetchUsers();
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      this.fetchUsers();
    },
    
    showAddUserDialog() {
      this.dialogTitle = '添加用户';
      this.isEdit = false;
      this.userForm = {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'viewer',
        status: 'active'
      };
      this.userDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.userForm) {
          this.$refs.userForm.clearValidate();
        }
      });
    },
    
    handleEdit(user) {
      this.dialogTitle = '编辑用户';
      this.isEdit = true;
      this.userForm = {
        id: user._id,
        username: user.username,
        email: user.email || '',
        role: user.role || 'viewer',
        status: user.status || 'active'
      };
      this.userDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.userForm) {
          this.$refs.userForm.clearValidate();
        }
      });
    },
    
    submitUserForm() {
      this.$refs.userForm.validate((valid) => {
        if (valid) {
          if (this.isEdit) {
            this.updateUser();
          } else {
            this.addUser();
          }
        } else {
          return false;
        }
      });
    },
    
    addUser() {
      const userData = {
        username: this.userForm.username,
        password: this.userForm.password,
        email: this.userForm.email,
        role: this.userForm.role,
        status: this.userForm.status
      };
      
      this.$axios.post('/api/register', userData)
        .then(response => {
          if (response.data.success) {
            this.$message.success('用户添加成功');
            this.userDialogVisible = false;
            this.fetchUsers();
          } else {
            this.$message.error(response.data.message || '用户添加失败');
          }
        })
        .catch(error => {
          this.$message.error('用户添加失败: ' + error.message);
        });
    },
    
    updateUser() {
      const userData = {
        email: this.userForm.email,
        role: this.userForm.role,
        status: this.userForm.status
      };
      
      this.$axios.put(`/api/users/${this.userForm.id}`, userData)
        .then(response => {
          if (response.data.success) {
            this.$message.success('用户更新成功');
            this.userDialogVisible = false;
            this.fetchUsers();
          } else {
            this.$message.error(response.data.message || '用户更新失败');
          }
        })
        .catch(error => {
          this.$message.error('用户更新失败: ' + error.message);
        });
    },
    
    handleToggleStatus(user) {
      const newStatus = user.status === 'active' ? 'disabled' : 'active';
      const statusText = newStatus === 'active' ? '启用' : '禁用';
      
      this.$confirm(`确定要${statusText}用户 ${user.username} 吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$axios.put(`/api/users/${user._id}`, { status: newStatus })
          .then(response => {
            if (response.data.success) {
              this.$message.success(`用户${statusText}成功`);
              this.fetchUsers();
            } else {
              this.$message.error(response.data.message || `用户${statusText}失败`);
            }
          })
          .catch(error => {
            this.$message.error(`用户${statusText}失败: ` + error.message);
          });
      }).catch(() => {});
    },
    
    handleDelete(user) {
      this.$confirm(`确定要删除用户 ${user.username} 吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$axios.delete(`/api/users/${user._id}`)
          .then(response => {
            if (response.data.success) {
              this.$message.success('用户删除成功');
              this.fetchUsers();
            } else {
              this.$message.error(response.data.message || '用户删除失败');
            }
          })
          .catch(error => {
            this.$message.error('用户删除失败: ' + error.message);
          });
      }).catch(() => {});
    },
    
    getRoleTagType(role) {
      switch (role) {
        case 'admin': return 'danger';
        case 'manager': return 'warning';
        case 'operator': return 'success';
        case 'viewer': return 'info';
        default: return 'info';
      }
    },
    
    getRoleText(role) {
      switch (role) {
        case 'admin': return '管理员';
        case 'manager': return '经理';
        case 'operator': return '操作员';
        case 'viewer': return '查看者';
        default: return role;
      }
    },
    
    getPermissionText(permission) {
      return this.permissionMap[permission] || permission;
    },
    
    fetchLogs() {
      this.logsLoading = true;
      
      let params = {
        limit: this.logPageSize,
        skip: (this.logCurrentPage - 1) * this.logPageSize
      };
      
      if (this.logUsername) {
        params.username = this.logUsername;
      }
      
      if (this.logActionType) {
        params.action_type = this.logActionType;
      }
      
      if (this.logDateRange && this.logDateRange.length === 2) {
        params.start_date = this.logDateRange[0].toISOString();
        params.end_date = this.logDateRange[1].toISOString();
      }
      
      this.$axios.get('/api/logs', { params })
        .then(response => {
          if (response.data.success) {
            this.logs = response.data.logs;
            this.totalLogs = response.data.total || this.logs.length;
          } else {
            this.$message.error(response.data.message || '获取日志失败');
          }
        })
        .catch(error => {
          this.$message.error('获取日志失败: ' + error.message);
        })
        .finally(() => {
          this.logsLoading = false;
        });
    },
    
    handleLogSizeChange(size) {
      this.logPageSize = size;
      this.fetchLogs();
    },
    
    handleLogCurrentChange(page) {
      this.logCurrentPage = page;
      this.fetchLogs();
    },
    
    resetLogFilters() {
      this.logUsername = '';
      this.logActionType = '';
      this.logDateRange = [];
      this.logCurrentPage = 1;
      this.fetchLogs();
    },
    
    showLogDetails(log) {
      this.logDetails = log.details;
      this.logDetailsVisible = true;
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    }
  },
  watch: {
    searchQuery() {
      this.applyFilters();
    }
  }
};
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.log-details {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}
</style> 