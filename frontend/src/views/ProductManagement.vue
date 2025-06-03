<template>
  <div class="product-management">
    <h1>商品管理</h1>
    
    <el-row :gutter="20" class="toolbar">
      <el-col :span="6">
        <el-input
          placeholder="搜索商品"
          v-model="searchQuery"
          clearable
          prefix-icon="el-icon-search">
        </el-input>
      </el-col>
      <el-col :span="12">
        <el-button-group>
          <el-button type="primary" icon="el-icon-plus" @click="showAddProductDialog">添加商品</el-button>
          <el-button type="success" icon="el-icon-upload" @click="showImportDialog">批量导入</el-button>
          <el-button type="info" icon="el-icon-download" @click="exportProducts">导出商品</el-button>
          <el-button type="warning" icon="el-icon-refresh" @click="refreshProducts">刷新</el-button>
        </el-button-group>
      </el-col>
      <el-col :span="6" style="text-align: right;">
        <el-dropdown @command="handleBatchCommand" split-button type="primary">
          批量操作
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="publish">批量上架</el-dropdown-item>
            <el-dropdown-item command="unpublish">批量下架</el-dropdown-item>
            <el-dropdown-item command="delete">批量删除</el-dropdown-item>
            <el-dropdown-item command="price">批量调价</el-dropdown-item>
            <el-dropdown-item command="polish">批量擦亮</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </el-col>
    </el-row>
    
    <el-tabs v-model="activeTab" @tab-click="handleTabClick">
      <el-tab-pane label="全部商品" name="all"></el-tab-pane>
      <el-tab-pane label="已上架" name="published"></el-tab-pane>
      <el-tab-pane label="未上架" name="draft"></el-tab-pane>
      <el-tab-pane label="已售出" name="sold"></el-tab-pane>
      <el-tab-pane label="已下架" name="unpublished"></el-tab-pane>
    </el-tabs>
    
    <el-table
      :data="filteredProducts"
      style="width: 100%"
      @selection-change="handleSelectionChange"
      v-loading="loading">
      <el-table-column
        type="selection"
        width="55">
      </el-table-column>
      <el-table-column
        prop="title"
        label="商品标题"
        min-width="250">
        <template slot-scope="scope">
          <div class="product-title">
            <el-image
              style="width: 50px; height: 50px"
              :src="scope.row.images && scope.row.images.length > 0 ? scope.row.images[0] : ''"
              fit="cover"
              :preview-src-list="scope.row.images">
            </el-image>
            <span class="title-text">{{ scope.row.title }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column
        prop="price"
        label="价格"
        width="100">
        <template slot-scope="scope">
          <span class="price">¥{{ scope.row.price.toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        prop="status"
        label="状态"
        width="100">
        <template slot-scope="scope">
          <el-tag :type="getStatusTagType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="category"
        label="分类"
        width="120">
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
        label="操作"
        width="200">
        <template slot-scope="scope">
          <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button size="mini" type="success" @click="handlePublish(scope.row)" v-if="scope.row.status === 'draft'">上架</el-button>
          <el-button size="mini" type="warning" @click="handleUnpublish(scope.row)" v-if="scope.row.status === 'published'">下架</el-button>
          <el-button size="mini" type="danger" @click="handleDelete(scope.row)">删除</el-button>
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
        :total="totalProducts">
      </el-pagination>
    </div>
    
    <!-- 添加/编辑商品对话框 -->
    <el-dialog :title="dialogTitle" :visible.sync="productDialogVisible" width="70%">
      <el-form :model="productForm" :rules="productRules" ref="productForm" label-width="100px">
        <el-form-item label="商品标题" prop="title">
          <el-input v-model="productForm.title" placeholder="请输入商品标题"></el-input>
        </el-form-item>
        <el-form-item label="商品价格" prop="price">
          <el-input-number v-model="productForm.price" :precision="2" :step="0.01" :min="0"></el-input-number>
        </el-form-item>
        <el-form-item label="商品分类" prop="category">
          <el-select v-model="productForm.category" placeholder="请选择商品分类">
            <el-option v-for="item in categories" :key="item" :label="item" :value="item"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="商品标签" prop="tags">
          <el-select v-model="productForm.tags" multiple placeholder="请选择商品标签">
            <el-option v-for="item in tags" :key="item" :label="item" :value="item"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="商品图片" prop="images">
          <el-upload
            action="/api/upload/image"
            list-type="picture-card"
            :file-list="imageFileList"
            :on-preview="handlePictureCardPreview"
            :on-remove="handleRemove"
            :on-success="handleUploadSuccess"
            :headers="uploadHeaders">
            <i class="el-icon-plus"></i>
          </el-upload>
          <el-dialog :visible.sync="dialogImageVisible">
            <img width="100%" :src="dialogImageUrl" alt="">
          </el-dialog>
        </el-form-item>
        <el-form-item label="商品描述" prop="description">
          <el-input type="textarea" v-model="productForm.description" :rows="6" placeholder="请输入商品描述"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="productDialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitProductForm">确 定</el-button>
      </div>
    </el-dialog>
    
    <!-- 导入商品对话框 -->
    <el-dialog title="批量导入商品" :visible.sync="importDialogVisible" width="50%">
      <el-upload
        class="upload-demo"
        drag
        action="/api/products/upload"
        :headers="uploadHeaders"
        :on-success="handleImportSuccess"
        :on-error="handleImportError"
        accept=".csv,.xlsx,.xls">
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">只能上传 Excel/CSV 文件</div>
      </el-upload>
      <div slot="footer" class="dialog-footer">
        <el-button @click="importDialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="downloadTemplate">下载模板</el-button>
      </div>
    </el-dialog>
    
    <!-- 批量调价对话框 -->
    <el-dialog title="批量调价" :visible.sync="priceDialogVisible" width="40%">
      <el-form :model="priceForm" label-width="100px">
        <el-form-item label="调价方式">
          <el-radio-group v-model="priceForm.mode">
            <el-radio :label="'percent'">百分比</el-radio>
            <el-radio :label="'fixed'">固定金额</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="调价值">
          <el-input-number 
            v-model="priceForm.value" 
            :precision="2" 
            :step="0.01"
            :min="priceForm.mode === 'percent' ? -100 : -9999">
          </el-input-number>
          <span v-if="priceForm.mode === 'percent'">%</span>
          <span v-else>元</span>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="priceDialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitPriceChange">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'ProductManagement',
  data() {
    return {
      searchQuery: '',
      products: [],
      filteredProducts: [],
      selectedProducts: [],
      loading: false,
      activeTab: 'all',
      currentPage: 1,
      pageSize: 10,
      totalProducts: 0,
      
      // 添加/编辑商品
      productDialogVisible: false,
      dialogTitle: '添加商品',
      productForm: {
        title: '',
        price: 0,
        category: '',
        tags: [],
        images: [],
        description: ''
      },
      productRules: {
        title: [
          { required: true, message: '请输入商品标题', trigger: 'blur' },
          { min: 3, max: 100, message: '长度在 3 到 100 个字符', trigger: 'blur' }
        ],
        price: [
          { required: true, message: '请输入商品价格', trigger: 'blur' }
        ],
        category: [
          { required: true, message: '请选择商品分类', trigger: 'change' }
        ],
        description: [
          { required: true, message: '请输入商品描述', trigger: 'blur' }
        ]
      },
      imageFileList: [],
      dialogImageUrl: '',
      dialogImageVisible: false,
      
      // 导入商品
      importDialogVisible: false,
      
      // 批量调价
      priceDialogVisible: false,
      priceForm: {
        mode: 'percent',
        value: 0
      },
      
      // 分类和标签
      categories: ['数码', '服装', '家居', '美妆', '其他'],
      tags: ['全新', '95新', '9成新', '8成新', '7成新', '二手', '闲置', '正品', '包邮', '特价']
    };
  },
  computed: {
    uploadHeaders() {
      return {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      };
    }
  },
  created() {
    this.fetchProducts();
  },
  methods: {
    fetchProducts() {
      this.loading = true;
      this.$axios.get('/api/products', {
        params: {
          page: this.currentPage,
          limit: this.pageSize,
          status: this.activeTab !== 'all' ? this.activeTab : undefined
        }
      })
        .then(response => {
          if (response.data.success) {
            this.products = response.data.products;
            this.totalProducts = response.data.total;
            this.applyFilters();
          } else {
            this.$message.error(response.data.message || '获取商品列表失败');
          }
        })
        .catch(error => {
          this.$message.error('获取商品列表失败: ' + error.message);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    
    applyFilters() {
      if (!this.searchQuery) {
        this.filteredProducts = this.products;
        return;
      }
      
      const query = this.searchQuery.toLowerCase();
      this.filteredProducts = this.products.filter(product => {
        return product.title.toLowerCase().includes(query) || 
               (product.description && product.description.toLowerCase().includes(query)) ||
               (product.category && product.category.toLowerCase().includes(query));
      });
    },
    
    refreshProducts() {
      this.fetchProducts();
    },
    
    handleTabClick() {
      this.currentPage = 1;
      this.fetchProducts();
    },
    
    handleSelectionChange(val) {
      this.selectedProducts = val;
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
      this.fetchProducts();
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      this.fetchProducts();
    },
    
    showAddProductDialog() {
      this.dialogTitle = '添加商品';
      this.productForm = {
        title: '',
        price: 0,
        category: '',
        tags: [],
        images: [],
        description: ''
      };
      this.imageFileList = [];
      this.productDialogVisible = true;
    },
    
    handleEdit(product) {
      this.dialogTitle = '编辑商品';
      this.productForm = { ...product };
      this.imageFileList = (product.images || []).map((url, index) => ({
        name: `图片${index + 1}`,
        url: url
      }));
      this.productDialogVisible = true;
    },
    
    submitProductForm() {
      this.$refs.productForm.validate((valid) => {
        if (valid) {
          const isEdit = !!this.productForm._id;
          const method = isEdit ? 'put' : 'post';
          const url = isEdit ? `/api/products/${this.productForm._id}` : '/api/products';
          
          this.$axios[method](url, this.productForm)
            .then(response => {
              if (response.data.success) {
                this.$message.success(isEdit ? '商品更新成功' : '商品添加成功');
                this.productDialogVisible = false;
                this.fetchProducts();
              } else {
                this.$message.error(response.data.message || (isEdit ? '商品更新失败' : '商品添加失败'));
              }
            })
            .catch(error => {
              this.$message.error((isEdit ? '商品更新失败: ' : '商品添加失败: ') + error.message);
            });
        } else {
          return false;
        }
      });
    },
    
    handleDelete(product) {
      this.$confirm('确定要删除该商品吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$axios.delete(`/api/products/${product._id}`)
          .then(response => {
            if (response.data.success) {
              this.$message.success('商品删除成功');
              this.fetchProducts();
            } else {
              this.$message.error(response.data.message || '商品删除失败');
            }
          })
          .catch(error => {
            this.$message.error('商品删除失败: ' + error.message);
          });
      }).catch(() => {});
    },
    
    handlePublish(product) {
      this.$axios.post(`/api/products/batch/publish`, {
        product_ids: [product._id]
      })
        .then(response => {
          if (response.data.success) {
            this.$message.success('商品上架成功');
            this.fetchProducts();
          } else {
            this.$message.error(response.data.message || '商品上架失败');
          }
        })
        .catch(error => {
          this.$message.error('商品上架失败: ' + error.message);
        });
    },
    
    handleUnpublish(product) {
      this.$axios.post(`/api/products/batch/unpublish`, {
        product_ids: [product._id]
      })
        .then(response => {
          if (response.data.success) {
            this.$message.success('商品下架成功');
            this.fetchProducts();
          } else {
            this.$message.error(response.data.message || '商品下架失败');
          }
        })
        .catch(error => {
          this.$message.error('商品下架失败: ' + error.message);
        });
    },
    
    handleBatchCommand(command) {
      if (this.selectedProducts.length === 0) {
        this.$message.warning('请先选择商品');
        return;
      }
      
      const productIds = this.selectedProducts.map(p => p._id);
      
      switch (command) {
        case 'publish':
          this.batchPublish(productIds);
          break;
        case 'unpublish':
          this.batchUnpublish(productIds);
          break;
        case 'delete':
          this.batchDelete(productIds);
          break;
        case 'price':
          this.showPriceDialog();
          break;
        case 'polish':
          this.batchPolish(productIds);
          break;
      }
    },
    
    batchPublish(productIds) {
      this.$axios.post('/api/products/batch/publish', { product_ids: productIds })
        .then(response => {
          if (response.data.success) {
            this.$message.success(`成功上架 ${response.data.count || productIds.length} 个商品`);
            this.fetchProducts();
          } else {
            this.$message.error(response.data.message || '批量上架失败');
          }
        })
        .catch(error => {
          this.$message.error('批量上架失败: ' + error.message);
        });
    },
    
    batchUnpublish(productIds) {
      this.$axios.post('/api/products/batch/unpublish', { product_ids: productIds })
        .then(response => {
          if (response.data.success) {
            this.$message.success(`成功下架 ${response.data.count || productIds.length} 个商品`);
            this.fetchProducts();
          } else {
            this.$message.error(response.data.message || '批量下架失败');
          }
        })
        .catch(error => {
          this.$message.error('批量下架失败: ' + error.message);
        });
    },
    
    batchDelete(productIds) {
      this.$confirm(`确定要删除选中的 ${productIds.length} 个商品吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$axios.post('/api/products/batch/delete', { product_ids: productIds })
          .then(response => {
            if (response.data.success) {
              this.$message.success(`成功删除 ${response.data.count || productIds.length} 个商品`);
              this.fetchProducts();
            } else {
              this.$message.error(response.data.message || '批量删除失败');
            }
          })
          .catch(error => {
            this.$message.error('批量删除失败: ' + error.message);
          });
      }).catch(() => {});
    },
    
    showPriceDialog() {
      this.priceForm = {
        mode: 'percent',
        value: 0
      };
      this.priceDialogVisible = true;
    },
    
    submitPriceChange() {
      const productIds = this.selectedProducts.map(p => p._id);
      
      this.$axios.post('/api/products/batch/price', {
        product_ids: productIds,
        mode: this.priceForm.mode,
        value: this.priceForm.value
      })
        .then(response => {
          if (response.data.success) {
            this.$message.success(`成功调整 ${response.data.count || productIds.length} 个商品价格`);
            this.priceDialogVisible = false;
            this.fetchProducts();
          } else {
            this.$message.error(response.data.message || '批量调价失败');
          }
        })
        .catch(error => {
          this.$message.error('批量调价失败: ' + error.message);
        });
    },
    
    batchPolish(productIds) {
      this.$axios.post('/api/tasks/polish', { product_ids: productIds })
        .then(response => {
          if (response.data.success) {
            this.$message.success(`成功擦亮 ${response.data.count || productIds.length} 个商品`);
            this.fetchProducts();
          } else {
            this.$message.error(response.data.message || '批量擦亮失败');
          }
        })
        .catch(error => {
          this.$message.error('批量擦亮失败: ' + error.message);
        });
    },
    
    showImportDialog() {
      this.importDialogVisible = true;
    },
    
    handleImportSuccess(response) {
      if (response.success) {
        this.$message.success(`成功导入 ${response.count} 个商品`);
        this.importDialogVisible = false;
        this.fetchProducts();
      } else {
        this.$message.error(response.message || '商品导入失败');
      }
    },
    
    handleImportError(err) {
      this.$message.error('商品导入失败: ' + err.message);
    },
    
    downloadTemplate() {
      window.open('/api/products/template/download', '_blank');
    },
    
    exportProducts() {
      const params = {
        status: this.activeTab !== 'all' ? this.activeTab : undefined
      };
      
      if (this.selectedProducts.length > 0) {
        params.product_ids = this.selectedProducts.map(p => p._id).join(',');
      }
      
      window.open(`/api/products/export?${new URLSearchParams(params).toString()}`, '_blank');
    },
    
    handlePictureCardPreview(file) {
      this.dialogImageUrl = file.url;
      this.dialogImageVisible = true;
    },
    
    handleRemove(file, fileList) {
      this.imageFileList = fileList;
      this.productForm.images = fileList.map(file => file.url);
    },
    
    handleUploadSuccess(response, file, fileList) {
      if (response.success) {
        this.imageFileList = fileList;
        this.productForm.images = fileList.map(file => {
          return file.response ? file.response.url : file.url;
        });
      } else {
        this.$message.error(response.message || '图片上传失败');
      }
    },
    
    getStatusTagType(status) {
      switch (status) {
        case 'published': return 'success';
        case 'draft': return 'info';
        case 'sold': return 'warning';
        case 'unpublished': return 'danger';
        default: return 'info';
      }
    },
    
    getStatusText(status) {
      switch (status) {
        case 'published': return '已上架';
        case 'draft': return '未上架';
        case 'sold': return '已售出';
        case 'unpublished': return '已下架';
        default: return '未知';
      }
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
.product-management {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.product-title {
  display: flex;
  align-items: center;
}

.title-text {
  margin-left: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.price {
  color: #f56c6c;
  font-weight: bold;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style> 